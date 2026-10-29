"""Sliding-window brute force detection.

For each source IP we keep the failures seen in the last `window_seconds`.
When the count crosses a threshold the stage escalates and ingest() returns a
DetectionResult. Same-stage or lower-stage events return None, so callers are
notified once per escalation, not once per log line.

Time handling: everything is based on EVENT time (the timestamp in the log),
not wall-clock time. That makes offline scans of old logs work and keeps
tests deterministic. Events are assumed to arrive roughly in order.
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Final

from sshblock.constants import (
    DEFAULT_ALERT_THRESHOLD,
    DEFAULT_BLOCK_THRESHOLD,
    DEFAULT_RATE_LIMIT_THRESHOLD,
    DEFAULT_WINDOW_SECONDS,
)
from sshblock.exceptions import ConfigError
from sshblock.models import AuthEvent, DetectionResult, EventType, ResponseStage

logger = logging.getLogger(__name__)

# MAX_AUTH_EXCEEDED is deliberately absent: it summarizes failures that were
# already logged (and counted) individually.
_COUNTED_TYPES: Final[frozenset[EventType]] = frozenset(
    {EventType.FAILED_PASSWORD, EventType.INVALID_USER}
)


@dataclass(frozen=True)
class DetectorConfig:
    """Tunable detection settings. Validated on creation."""

    window_seconds: int = DEFAULT_WINDOW_SECONDS
    alert_threshold: int = DEFAULT_ALERT_THRESHOLD
    rate_limit_threshold: int = DEFAULT_RATE_LIMIT_THRESHOLD
    block_threshold: int = DEFAULT_BLOCK_THRESHOLD
    sweep_interval_seconds: int = 60  # how often (in event time) to drop idle IPs
    max_tracked_ips: int = 10_000  # memory cap on distinct IPs
    max_events_per_ip: int = 1_000  # memory cap on history per IP

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ConfigError("window_seconds must be positive")
        if not 0 < self.alert_threshold < self.rate_limit_threshold < self.block_threshold:
            raise ConfigError(
                "thresholds must be positive and strictly ascending: "
                "alert < rate_limit < block"
            )
        if self.max_events_per_ip < self.block_threshold:
            raise ConfigError("max_events_per_ip must be at least block_threshold")
        if self.max_tracked_ips < 1:
            raise ConfigError("max_tracked_ips must be at least 1")
        if self.sweep_interval_seconds <= 0:
            raise ConfigError("sweep_interval_seconds must be positive")


@dataclass
class _IPState:
    """Everything the detector remembers about one source IP."""

    failures: deque[AuthEvent]
    stage: ResponseStage = ResponseStage.NONE
    # Source ports of connections already counted via an "Invalid user" line.
    pending_ports: set[int] = field(default_factory=set)


class BruteForceDetector:
    def __init__(self, config: DetectorConfig | None = None) -> None:
        self._config = config or DetectorConfig()
        self._window = timedelta(seconds=self._config.window_seconds)
        self._sweep_interval = timedelta(seconds=self._config.sweep_interval_seconds)
        self._states: dict[str, _IPState] = {}
        self._last_sweep: datetime | None = None

    # --- Public API --------------------------------------------------------
    def ingest(self, event: AuthEvent) -> DetectionResult | None:
        """Feed one event. Returns a result only when the IP's stage escalates."""
        now = event.timestamp
        self._maybe_sweep(now)

        if event.event_type not in _COUNTED_TYPES:
            return None

        state = self._states.get(event.ip)
        if state is None:
            state = self._new_state(event.ip)
        else:
            self._prune(state, now)

        # "Failed password for invalid user" right after "Invalid user" on the same
        # connection is the same attempt: absorb the first one instead of counting twice.
        port = event.port
        if (
            event.event_type is EventType.FAILED_PASSWORD
            and event.invalid_user
            and port is not None
            and port in state.pending_ports
        ):
            state.pending_ports.discard(port)
            return None

        state.failures.append(event)
        if event.event_type is EventType.INVALID_USER and event.port is not None:
            state.pending_ports.add(event.port)

        new_stage = self._stage_for(len(state.failures))
        if new_stage <= state.stage:
            return None
        state.stage = new_stage
        return DetectionResult(
            ip=event.ip,
            failures=len(state.failures),
            window_seconds=self._config.window_seconds,
            first_seen=state.failures[0].timestamp,
            last_seen=event.timestamp,
            stage=new_stage,
            usernames={e.username for e in state.failures if e.username},
        )

    def sweep(self, now: datetime) -> int:
        """Drop IPs with no failures left in the window. Returns how many were removed."""
        removed = 0
        for ip in list(self._states):
            state = self._states[ip]
            self._prune(state, now)
            if not state.failures:
                del self._states[ip]
                removed += 1
        self._last_sweep = now
        return removed

    def reset(self, ip: str) -> None:
        """Forget an IP entirely (e.g. after a manual unblock)."""
        self._states.pop(ip, None)

    def snapshot(self) -> dict[str, int]:
        """Current failure count per tracked IP (as of the last event or sweep)."""
        return {ip: len(state.failures) for ip, state in self._states.items()}

    # --- Internals ---------------------------------------------------------
    def _stage_for(self, failures: int) -> ResponseStage:
        cfg = self._config
        if failures >= cfg.block_threshold:
            return ResponseStage.BLOCK
        if failures >= cfg.rate_limit_threshold:
            return ResponseStage.RATE_LIMIT
        if failures >= cfg.alert_threshold:
            return ResponseStage.ALERT
        return ResponseStage.NONE

    def _prune(self, state: _IPState, now: datetime) -> None:
        """Drop failures older than the window, and de-escalate if the attack died down."""
        cutoff = now - self._window
        while state.failures and state.failures[0].timestamp <= cutoff:
            state.failures.popleft()
        if not state.failures:
            state.pending_ports.clear()
        # Lowering the stage lets a returning attacker trigger a fresh alert.
        current = self._stage_for(len(state.failures))
        if current < state.stage:
            state.stage = current

    def _maybe_sweep(self, now: datetime) -> None:
        if self._last_sweep is None:
            self._last_sweep = now
        elif now - self._last_sweep >= self._sweep_interval:
            self.sweep(now)

    def _new_state(self, ip: str) -> _IPState:
        if len(self._states) >= self._config.max_tracked_ips:
            self._evict_least_recent()
        state = _IPState(failures=deque(maxlen=self._config.max_events_per_ip))
        self._states[ip] = state
        return state

    def _evict_least_recent(self) -> None:
        """Table full: drop the IP whose latest failure is oldest."""
        victim = min(self._states, key=lambda ip: self._states[ip].failures[-1].timestamp)
        logger.warning("Tracking table full; evicting %s", victim)
        del self._states[victim]