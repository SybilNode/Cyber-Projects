from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from sshblock.models import (
    AuthEvent,
    BlockRecord,
    DetectionResult,
    EventType,
    ResponseStage,
)

NOW = datetime(2026, 10, 26, 14, 3, 22)


def make_event(event_type: EventType = EventType.FAILED_PASSWORD) -> AuthEvent:
    return AuthEvent(timestamp=NOW, ip="203.0.113.5", username="root", event_type=event_type)


def test_stages_are_ordered():
    assert ResponseStage.NONE < ResponseStage.ALERT < ResponseStage.RATE_LIMIT < ResponseStage.BLOCK


def test_event_type_is_a_string():
    assert EventType.FAILED_PASSWORD == "failed_password"


@pytest.mark.parametrize(
    "event_type, expected",
    [
        (EventType.FAILED_PASSWORD, True),
        (EventType.INVALID_USER, True),
        (EventType.MAX_AUTH_EXCEEDED, True),
        (EventType.ACCEPTED, False),
        (EventType.PREAUTH_DISCONNECT, False),
    ],
)
def test_is_failure(event_type, expected):
    assert make_event(event_type).is_failure is expected


def test_auth_event_is_immutable():
    event = make_event()
    with pytest.raises(FrozenInstanceError):
        event.ip = "198.51.100.9"  # type: ignore[misc]


def test_auth_event_is_hashable():
    assert len({make_event(), make_event()}) == 1  # equal frozen events collapse


def test_detection_results_do_not_share_usernames():
    a = DetectionResult(ip="1.1.1.1", failures=1, window_seconds=600,
                        first_seen=NOW, last_seen=NOW, stage=ResponseStage.NONE)
    b = DetectionResult(ip="2.2.2.2", failures=1, window_seconds=600,
                        first_seen=NOW, last_seen=NOW, stage=ResponseStage.NONE)
    a.usernames.add("root")
    assert b.usernames == set()


def test_block_record_defaults_to_permanent():
    rec = BlockRecord(ip="1.1.1.1", stage=ResponseStage.BLOCK, reason="test",
                      created_at=NOW, failure_count=20)
    assert rec.expires_at is None