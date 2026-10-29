from datetime import datetime, timezone

import pytest

from sshblock.exceptions import LogParseError
from sshblock.models import EventType
from sshblock.parser import parse_file, parse_line, parse_timestamp, validate_ip

PREFIX = "Oct 26 14:03:22 myhost sshd[1234]: "


def parse(message: str, prefix: str = PREFIX):
    return parse_line(prefix + message, reference_year=2026)


@pytest.mark.parametrize(
    "message, event_type, ip, username, port, method, invalid",
    [
        ("Failed password for root from 203.0.113.5 port 50022 ssh2",
         EventType.FAILED_PASSWORD, "203.0.113.5", "root", 50022, "password", False),
        ("Failed password for invalid user admin from 203.0.113.5 port 50022 ssh2",
         EventType.FAILED_PASSWORD, "203.0.113.5", "admin", 50022, "password", True),
        ("Invalid user admin from 203.0.113.5 port 50022",
         EventType.INVALID_USER, "203.0.113.5", "admin", 50022, None, True),
        ("Invalid user admin from 203.0.113.5",
         EventType.INVALID_USER, "203.0.113.5", "admin", None, None, True),
        ("Accepted password for bob from 198.51.100.7 port 22 ssh2",
         EventType.ACCEPTED, "198.51.100.7", "bob", 22, "password", False),
        ("Accepted publickey for bob from 198.51.100.7 port 41000 ssh2: RSA SHA256:abc123",
         EventType.ACCEPTED, "198.51.100.7", "bob", 41000, "publickey", False),
        ("Connection closed by authenticating user root 203.0.113.5 port 50022 [preauth]",
         EventType.PREAUTH_DISCONNECT, "203.0.113.5", "root", 50022, None, False),
        ("Connection closed by invalid user admin 203.0.113.5 port 50022 [preauth]",
         EventType.PREAUTH_DISCONNECT, "203.0.113.5", "admin", 50022, None, True),
        ("error: maximum authentication attempts exceeded for root from 203.0.113.5"
         " port 50022 ssh2 [preauth]",
         EventType.MAX_AUTH_EXCEEDED, "203.0.113.5", "root", 50022, None, False),
        ("Failed password for root from 2001:db8::1 port 50022 ssh2",
         EventType.FAILED_PASSWORD, "2001:db8::1", "root", 50022, "password", False),
        ("Failed password for root from ::ffff:203.0.113.5 port 50022 ssh2",
         EventType.FAILED_PASSWORD, "203.0.113.5", "root", 50022, "password", False),
    ],
)
def test_parses_each_line_type(message, event_type, ip, username, port, method, invalid):
    event = parse(message)
    assert event is not None
    assert event.event_type is event_type
    assert event.ip == ip
    assert event.username == username
    assert event.port == port
    assert event.method == method
    assert event.invalid_user is invalid
    assert event.raw == PREFIX + message


def test_iso_timestamp_is_converted_to_naive_local_time():
    line = ("2026-10-26T14:03:22.123456+00:00 myhost sshd[1]: "
            "Failed password for root from 203.0.113.5 port 22 ssh2")
    event = parse_line(line)
    expected = (datetime(2026, 10, 26, 14, 3, 22, 123456, tzinfo=timezone.utc)
                .astimezone().replace(tzinfo=None))
    assert event is not None
    assert event.timestamp == expected
    assert event.timestamp.tzinfo is None


def test_sshd_session_program_name_is_accepted():
    event = parse("Failed password for root from 203.0.113.5 port 22 ssh2",
                  prefix="Oct 26 14:03:22 myhost sshd-session[99]: ")
    assert event is not None


# --- Log injection ---------------------------------------------------------
def test_failed_password_username_cannot_spoof_ip():
    event = parse("Failed password for x from 8.8.8.8 port 22 from 203.0.113.5 port 50022 ssh2")
    assert event is not None
    assert event.ip == "203.0.113.5"  # NOT 8.8.8.8
    assert event.username == "x from 8.8.8.8 port 22"


def test_invalid_user_username_cannot_spoof_ip():
    event = parse("Invalid user x from 8.8.8.8 port 22 from 203.0.113.5 port 50022")
    assert event is not None
    assert event.ip == "203.0.113.5"
    assert event.username == "x from 8.8.8.8 port 22"


def test_preauth_username_cannot_spoof_ip():
    event = parse("Connection closed by authenticating user x 8.8.8.8 port 22 [preauth]"
                  " 203.0.113.5 port 50022 [preauth]")
    assert event is not None
    assert event.ip == "203.0.113.5"


# --- Lines that must be ignored --------------------------------------------
@pytest.mark.parametrize(
    "line",
    [
        "",
        "garbage",
        "Oct 26 14:03:22 myhost sudo: bob : TTY=pts/0 ; COMMAND=/bin/ls",
        PREFIX + "Server listening on 0.0.0.0 port 22.",
        PREFIX + "Failed password for root from 999.1.1.1 port 22 ssh2",   # invalid IP
        PREFIX + "Failed password for root from evil.example.com port 22 ssh2",  # hostname
        PREFIX + "Failed password for root from 203.0.113.5 port 22 ssh2 trailing junk",
        "Foo 99 99:99:99 myhost sshd[1]: Failed password for root from 1.2.3.4 port 22 ssh2",
    ],
)
def test_unrecognized_or_malformed_lines_return_none(line):
    assert parse_line(line, reference_year=2026) is None


# --- Timestamps ------------------------------------------------------------
def test_syslog_timestamp_with_reference_year():
    assert parse_timestamp("Oct 26 14:03:22", 2026) == datetime(2026, 10, 26, 14, 3, 22)


def test_syslog_single_digit_day_is_space_padded():
    assert parse_timestamp("Oct  6 09:00:00", 2026) == datetime(2026, 10, 6, 9, 0, 0)


def test_year_inferred_as_current_year():
    now = datetime(2026, 10, 26, 15, 0, 0)
    assert parse_timestamp("Oct 26 14:03:22", now=now) == datetime(2026, 10, 26, 14, 3, 22)


def test_year_rollover_dec_to_jan():
    now = datetime(2027, 1, 2, 0, 5, 0)
    assert parse_timestamp("Dec 31 23:59:59", now=now) == datetime(2026, 12, 31, 23, 59, 59)


def test_leap_day_falls_back_to_previous_year():
    now = datetime(2025, 3, 1, 0, 0, 0)
    assert parse_timestamp("Feb 29 12:00:00", now=now) == datetime(2024, 2, 29, 12, 0, 0)


def test_bad_timestamp_raises():
    with pytest.raises(LogParseError):
        parse_timestamp("Foo 99 99:99:99", 2026)


@pytest.mark.parametrize("bad", ["999.1.1.1", "not-an-ip", ""])
def test_validate_ip_rejects_garbage(bad):
    with pytest.raises(LogParseError):
        validate_ip(bad)


# --- parse_file ------------------------------------------------------------
def test_parse_file_yields_only_events_in_order(tmp_path):
    log = tmp_path / "auth.log"
    log.write_text(
        "\n".join([
            "Oct 26 14:03:22 h sshd[1]: Failed password for root from 203.0.113.5 port 22 ssh2",
            "Oct 26 14:03:23 h sudo: bob : COMMAND=/bin/ls",
            "Oct 26 14:03:24 h sshd[1]: Invalid user admin from 203.0.113.5 port 22",
            "Oct 26 14:03:25 h sshd[1]: Accepted password for bob from 198.51.100.7 port 22 ssh2",
        ]) + "\n",
        encoding="utf-8",
    )
    events = list(parse_file(log, reference_year=2026))
    assert [e.event_type for e in events] == [
        EventType.FAILED_PASSWORD, EventType.INVALID_USER, EventType.ACCEPTED,
    ]