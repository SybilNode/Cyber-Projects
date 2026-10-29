"""Parse sshd log lines into AuthEvent objects.

Two-step approach:
  1. HEADER regex: split "<timestamp> <host> sshd[pid]: <message>".
  2. MESSAGE regexes: classify the message and pull out user, IP, port.

Security note: the username is attacker-controlled and may contain spaces.
Every message regex is anchored with $ and uses a greedy username group, so
the LAST "from <ip> port <n>" on the line (the one sshd wrote) always wins.
"""

import ipaddress
import logging
import re
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path
from typing import Final

from sshblock.exceptions import LogParseError
from sshblock.models import AuthEvent, EventType

logger = logging.getLogger(__name__)

# --- Regexes ---------------------------------------------------------------
# Matches both "Oct 26 14:03:22" (syslog) and "2026-10-26T14:03:22+00:00" (ISO).
_HEADER_RE: Final = re.compile(
    r"^(?P<ts>"
    r"[A-Z][a-z]{2}\s+\d{1,2}\s\d{2}:\d{2}:\d{2}"
    r"|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?"
    r")\s+\S+\s+sshd(?:-session)?(?:\[\d+\])?:\s+(?P<msg>.*)$"
)

_IP = r"(?P<ip>[0-9A-Fa-f:.]+)"  # loose shape only; validate_ip() does the real check
_PORT = r"(?P<port>\d+)"
# Optional "ssh2" and, for key logins, "ssh2: RSA SHA256:abc...". Deliberately strict:
# anything unexpected after the port makes the line not match (fail safe).
_TAIL = r"(?: ssh2(?:: \S+ \S+)?)?"

_MESSAGE_PATTERNS: Final[tuple[tuple[EventType, re.Pattern[str]], ...]] = (
    (
        EventType.FAILED_PASSWORD,
        re.compile(
            rf"^Failed (?P<method>\S+) for (?P<invalid>invalid user )?(?P<user>.+)"
            rf" from {_IP} port {_PORT}{_TAIL}$"
        ),
    ),
    (
        EventType.INVALID_USER,
        re.compile(rf"^Invalid user (?P<user>.+) from {_IP}(?: port {_PORT})?$"),
    ),
    (
        EventType.ACCEPTED,
        re.compile(
            rf"^Accepted (?P<method>\S+) for (?P<user>.+) from {_IP} port {_PORT}{_TAIL}$"
        ),
    ),
    (
        EventType.PREAUTH_DISCONNECT,
        re.compile(
            r"^(?:Connection closed by|Disconnected from) "
            r"(?:(?:authenticating|(?P<invalid>invalid)) user (?P<user>.+) )?"
            rf"{_IP} port {_PORT} \[preauth\]$"
        ),
    ),
    (
        EventType.MAX_AUTH_EXCEEDED,
        re.compile(
            r"^(?:error: )?maximum authentication attempts exceeded for "
            rf"(?P<invalid>invalid user )?(?P<user>.+) from {_IP} port {_PORT}"
            r" ssh2(?: \[preauth\])?$"
        ),
    ),
)

_SYSLOG_FORMAT: Final = "%Y %b %d %H:%M:%S"  # year is prepended before parsing
_FUTURE_TOLERANCE: Final = timedelta(days=1)  # allows for clock skew


# --- Helpers ---------------------------------------------------------------
def validate_ip(candidate: str) -> str:
    """Return the normalized IP string, or raise LogParseError.

    IPv4-mapped IPv6 addresses (::ffff:1.2.3.4) are converted to plain IPv4 so
    whitelist and firewall comparisons see one canonical form.
    """
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError as exc:
        raise LogParseError(f"not a valid IP address: {candidate!r}") from exc
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        address = address.ipv4_mapped
    return str(address)


def _parse_syslog(raw: str, year: int) -> datetime:
    try:
        return datetime.strptime(f"{year} {raw}", _SYSLOG_FORMAT)
    except ValueError as exc:
        raise LogParseError(f"bad syslog timestamp: {raw!r}") from exc


def parse_timestamp(
    raw: str, reference_year: int | None = None, now: datetime | None = None
) -> datetime:
    """Convert a log timestamp to a naive local datetime.

    ISO timestamps carry a year (and usually a timezone, which is converted to
    local time). Syslog timestamps have no year, so we either use
    `reference_year` or infer it: try the current year, and if that lands in
    the future, the line must be from last year (the Dec -> Jan boundary).
    """
    raw = raw.strip()

    if raw[:4].isdigit():  # ISO 8601
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise LogParseError(f"bad ISO timestamp: {raw!r}") from exc
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone().replace(tzinfo=None)
        return parsed

    if reference_year is not None:
        return _parse_syslog(raw, reference_year)

    current = now or datetime.now()
    # Trying year-1 as a fallback also handles Feb 29 when this year isn't a leap year.
    for year in (current.year, current.year - 1):
        try:
            candidate = _parse_syslog(raw, year)
        except LogParseError:
            continue
        if candidate <= current + _FUTURE_TOLERANCE:
            return candidate
    raise LogParseError(f"cannot infer a year for timestamp: {raw!r}")


def _match_message(message: str) -> tuple[EventType, re.Match[str]] | None:
    for event_type, pattern in _MESSAGE_PATTERNS:
        match = pattern.match(message)
        if match is not None:
            return event_type, match
    return None


# --- Public API ------------------------------------------------------------
def parse_line(
    line: str, *, reference_year: int | None = None, now: datetime | None = None
) -> AuthEvent | None:
    """Parse one log line. Returns None for anything that isn't a recognized sshd event."""
    line = line.rstrip("\r\n")

    header = _HEADER_RE.match(line)
    if header is None:
        return None  # not an sshd line (auth.log is full of sudo, cron, ...)

    found = _match_message(header.group("msg"))
    if found is None:
        return None  # sshd line we don't care about
    event_type, match = found
    groups = match.groupdict()

    try:
        ip = validate_ip(groups["ip"])
        timestamp = parse_timestamp(header.group("ts"), reference_year, now)
    except LogParseError as exc:
        logger.debug("Skipping line: %s", exc)
        return None

    port = groups.get("port")
    return AuthEvent(
        timestamp=timestamp,
        ip=ip,
        username=groups.get("user") or "",
        event_type=event_type,
        port=int(port) if port else None,
        method=groups.get("method"),
        raw=line,
        invalid_user=bool(groups.get("invalid")) or event_type is EventType.INVALID_USER,
    )


def parse_file(path: Path, *, reference_year: int | None = None) -> Iterator[AuthEvent]:
    """Yield every recognized event in a log file (one-shot analysis)."""
    # errors="replace": attackers can write junk bytes into logs; never crash on them.
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            event = parse_line(line, reference_year=reference_year)
            if event is not None:
                yield event