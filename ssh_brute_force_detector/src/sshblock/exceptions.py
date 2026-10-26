"""Custom exception hierarchy for sshblock.

Every error raised deliberately by this project inherits from SSHBlockError,
so callers can catch the whole family with a single except clause.
"""


class SSHBlockError(Exception):
    """Base class for all sshblock errors."""


class ConfigError(SSHBlockError):
    """The configuration file is missing, malformed, or fails validation."""


class LogParseError(SSHBlockError):
    """A log line or file could not be parsed."""


class FirewallError(SSHBlockError):
    """A firewall command failed, or the required tool/privileges are missing."""


class UnsafeBlockError(SSHBlockError):
    """A block was refused by a safeguard (own IP, whitelist, circuit breaker)."""