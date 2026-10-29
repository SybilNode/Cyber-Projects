from datetime import datetime, timedelta

import pytest

from sshblock.detector import BruteForceDetector, DetectorConfig
from sshblock.exceptions import ConfigError
from sshblock.models import AuthEvent, EventType, ResponseStage

BASE = datetime(2026, 10, 26, 14, 0, 0)
IP = "203.0.113.5"


def ev(
    seconds: int = 0,
    *,
    ip: str = IP,
    user: str = "root",
    event_type: EventType = EventType.FAILED_PASSWORD,
    port: int | None = None,
    invalid: bool = False,
) -> AuthEvent:
    return AuthEvent(
        timestamp=BASE + timedelta(seconds=seconds),
        ip=ip,
        username=user,
        event_type=event_type,
        port=port,
        invalid_user=invalid,
    )


def test_five_quick_failures_trigger_alert():
    detector = BruteForceDetector()
    results = [detector.ingest(ev(i)) for i in range(5)]
    assert results[:4] == [None] * 4
    assert results[4] is not None
    assert results[4].stage is ResponseStage.ALERT
    assert results[4].failures == 5


def test_failures_spread_over_time_do_not_trigger():
    detector = BruteForceDetector()
    results = [detector.ingest(ev(i * 1800)) for i in range(5)]  # one every 30 minutes
    assert results == [None] * 5


def test_only_escalations_return_a_result():
    detector = BruteForceDetector()
    stages = {}
    for i in range(30):
        result = detector.ingest(ev(i))
        if result is not None:
            stages[i + 1] = result.stage
    assert stages == {
        5: ResponseStage.ALERT,
        10: ResponseStage.RATE_LIMIT,
        20: ResponseStage.BLOCK,
    }


@pytest.mark.parametrize("gap, expect_alert", [(599, True), (600, False)])
def test_window_boundary(gap, expect_alert):
    config = DetectorConfig(alert_threshold=2, rate_limit_threshold=3, block_threshold=4)
    detector = BruteForceDetector(config)
    assert detector.ingest(ev(0)) is None
    result = detector.ingest(ev(gap))
    assert (result is not None) is expect_alert


def test_ips_are_tracked_independently():
    detector = BruteForceDetector()
    for i in range(4):
        assert detector.ingest(ev(i, ip="10.0.0.1")) is None
        assert detector.ingest(ev(i, ip="10.0.0.2")) is None
    assert detector.snapshot() == {"10.0.0.1": 4, "10.0.0.2": 4}


def test_invalid_user_pair_on_same_connection_counts_once():
    detector = BruteForceDetector()
    for i in range(4):
        detector.ingest(ev(i * 2, event_type=EventType.INVALID_USER,
                           port=5000 + i, user="admin", invalid=True))
        detector.ingest(ev(i * 2 + 1, event_type=EventType.FAILED_PASSWORD,
                           port=5000 + i, user="admin", invalid=True))
    assert detector.snapshot() == {IP: 4}  # 8 lines, 4 attempts

    first = detector.ingest(ev(10, event_type=EventType.INVALID_USER,
                               port=5004, user="admin", invalid=True))
    assert first is not None and first.stage is ResponseStage.ALERT and first.failures == 5
    assert detector.ingest(ev(11, port=5004, user="admin", invalid=True)) is None
    assert detector.snapshot() == {IP: 5}


def test_extra_attempts_on_same_connection_still_count():
    detector = BruteForceDetector()
    detector.ingest(ev(0, event_type=EventType.INVALID_USER, port=6000, invalid=True))
    for i in range(1, 4):
        detector.ingest(ev(i, port=6000, invalid=True))
    # Invalid user (1) + 3 failed passwords, the first absorbed -> 3 attempts.
    assert detector.snapshot() == {IP: 3}


@pytest.mark.parametrize(
    "event_type",
    [EventType.ACCEPTED, EventType.MAX_AUTH_EXCEEDED, EventType.PREAUTH_DISCONNECT],
)
def test_non_failure_events_are_ignored(event_type):
    detector = BruteForceDetector()
    assert detector.ingest(ev(0, event_type=event_type)) is None
    assert detector.snapshot() == {}


def test_can_alert_again_after_quiet_period():
    detector = BruteForceDetector()
    first = [detector.ingest(ev(i)) for i in range(5)]
    assert first[-1] is not None
    later = [detector.ingest(ev(1200 + i)) for i in range(5)]  # 20 minutes later
    assert later[:4] == [None] * 4
    assert later[4] is not None and later[4].stage is ResponseStage.ALERT


def test_sweep_removes_idle_ips():
    detector = BruteForceDetector()
    detector.ingest(ev(0))
    assert detector.sweep(BASE + timedelta(seconds=601)) == 1
    assert detector.snapshot() == {}


def test_ingest_sweeps_automatically():
    detector = BruteForceDetector()
    detector.ingest(ev(0, ip="10.0.0.1"))
    detector.ingest(ev(700, ip="10.0.0.2"))  # 700s later: idle 10.0.0.1 is swept
    assert detector.snapshot() == {"10.0.0.2": 1}


def test_oldest_ip_evicted_when_table_full():
    detector = BruteForceDetector(DetectorConfig(max_tracked_ips=3))
    for i, ip in enumerate(["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4"]):
        detector.ingest(ev(i, ip=ip))
    assert set(detector.snapshot()) == {"10.0.0.2", "10.0.0.3", "10.0.0.4"}


def test_events_per_ip_are_capped():
    detector = BruteForceDetector(DetectorConfig(max_events_per_ip=50))
    for i in range(200):
        detector.ingest(ev(i))
    assert detector.snapshot() == {IP: 50}


def test_reset_forgets_ip():
    detector = BruteForceDetector()
    for i in range(3):
        detector.ingest(ev(i))
    detector.reset(IP)
    detector.reset("198.51.100.1")  # unknown IP: no error
    assert detector.snapshot() == {}


def test_result_describes_the_attack():
    detector = BruteForceDetector()
    users = ["root", "admin", "root", "test", "oracle"]
    results = [detector.ingest(ev(i, user=u)) for i, u in enumerate(users)]
    result = results[-1]
    assert result is not None
    assert result.ip == IP
    assert result.usernames == {"root", "admin", "test", "oracle"}
    assert result.first_seen == BASE
    assert result.last_seen == BASE + timedelta(seconds=4)
    assert result.window_seconds == 600


@pytest.mark.parametrize(
    "kwargs",
    [
        {"window_seconds": 0},
        {"alert_threshold": 10, "rate_limit_threshold": 10},  # not strictly ascending
        {"alert_threshold": 0},
        {"max_events_per_ip": 5},  # below block_threshold
        {"max_tracked_ips": 0},
    ],
)
def test_invalid_config_is_rejected(kwargs):
    with pytest.raises(ConfigError):
        DetectorConfig(**kwargs)