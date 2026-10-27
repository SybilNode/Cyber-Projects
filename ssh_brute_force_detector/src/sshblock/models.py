"""Core data models shared across sshblock.

Pipeline:  log line -> AuthEvent -> DetectionResult -> BlockRecord
           (parser)    (detector)    (responder / storage)

Timestamps are naive local datetimes, because classic syslog lines carry no
timezone. They are used consistently everywhere so comparisons stay valid.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Final


class EventType(StrEnum):
    """What kind of SSH authentication event a log line describes."""

    FAILED_PASSWORD = "failed_password"
    INVALID_USER = "invalid_user"
    ACCEPTED = "accepted"
    PREAUTH_DISCONNECT = "preauth_disconnect"
    MAX_AUTH_EXCEEDED = "max_auth_exceeded"


# Event types that count toward brute force thresholds.
# NOTE: one bad attempt against a nonexistent user can produce BOTH an
# "Invalid user" line and a "Failed password for invalid user" line.
# We will deal with that double-counting in Phase 4 (detector).
FAILURE_EVENT_TYPES: Final[frozenset[EventType]] = frozenset(
    {
        EventType.FAILED_PASSWORD,
        EventType.INVALID_USER,
        EventType.MAX_AUTH_EXCEEDED,
    }
)


class ResponseStage(IntEnum):
    """Escalation level for an IP. Higher number = stronger response."""

    NONE = 0
    ALERT = 1
    RATE_LIMIT = 2
    BLOCK = 3


@dataclass(frozen=True, slots=True)
class AuthEvent:
    """One parsed SSH authentication event. Immutable."""

    timestamp: datetime
    ip: str
    username: str
    event_type: EventType
    port: int | None = None
    method: str | None = None  # "password", "publickey", ...
    raw: str = ""  # original log line, kept for audit and debugging
    invalid_user: bool = False  # True if the username doesn't exist on the system

    @property
    def is_failure(self) -> bool:
        """True if this event counts toward brute force detection."""
        return self.event_type in FAILURE_EVENT_TYPES


@dataclass
class DetectionResult:
    """The detector's verdict about one IP within the sliding window."""

    ip: str
    failures: int
    window_seconds: int
    first_seen: datetime
    last_seen: datetime
    stage: ResponseStage
    usernames: set[str] = field(default_factory=set)


@dataclass
class BlockRecord:
    """A response action taken against an IP, persisted so it survives restarts."""

    ip: str
    stage: ResponseStage
    reason: str
    created_at: datetime
    failure_count: int
    expires_at: datetime | None = None  # None = permanent (e.g. blacklist)