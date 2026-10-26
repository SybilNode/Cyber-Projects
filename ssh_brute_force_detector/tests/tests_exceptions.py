import pytest

from ssh_brute_force_detector.src.sshblock.exceptions import (
    ConfigError,
    FirewallError,
    LogParseError,
    SSHBlockError,
    UnsafeBlockError,
)


@pytest.mark.parametrize("exc", [ConfigError, LogParseError, FirewallError, UnsafeBlockError])
def test_all_errors_share_base_class(exc):
    assert issubclass(exc, SSHBlockError)


def test_base_class_catches_children():
    with pytest.raises(SSHBlockError):
        raise UnsafeBlockError("refusing to block loopback")