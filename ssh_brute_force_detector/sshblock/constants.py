"""Default values and fixed settings for sshblock.

Anything here can be overridden by the TOML config (Phase 11); these are
the fallbacks used when the user hasn't configured anything.
"""

from pathlib import Path
from typing import Final

# --- Log locations -------------------------------------------------------
# Debian/Ubuntu write to auth.log; RedHat/CentOS/Fedora write to secure.
DEFAULT_LOG_PATHS: Final[tuple[Path, ...]] = (
    Path("/var/log/auth.log"),
    Path("/var/log/secure"),
)

# --- Detection thresholds ------------------------------------------------
# Failures from one IP within the window trigger each escalation stage.
# These must be strictly ascending (validated in config.py).
DEFAULT_WINDOW_SECONDS: Final[int] = 600       # 10-minute sliding window
DEFAULT_ALERT_THRESHOLD: Final[int] = 5        # stage 1: notify admins
DEFAULT_RATE_LIMIT_THRESHOLD: Final[int] = 10  # stage 2: throttle the IP
DEFAULT_BLOCK_THRESHOLD: Final[int] = 20       # stage 3: drop all packets

# --- Block lifetime ------------------------------------------------------
DEFAULT_BLOCK_TTL_HOURS: Final[int] = 24

# --- Monitoring ----------------------------------------------------------
DEFAULT_POLL_INTERVAL_SECONDS: Final[float] = 1.0
DEFAULT_SSH_PORT: Final[int] = 22

# --- Safeguards ----------------------------------------------------------
MAX_BLOCKS_PER_HOUR: Final[int] = 50  # circuit breaker (Phase 6)

# --- Firewall ------------------------------------------------------------
FIREWALL_CHAIN_NAME: Final[str] = "SSHBLOCK"
FIREWALL_COMMAND_TIMEOUT_SECONDS: Final[int] = 10

# --- Persistence ---------------------------------------------------------
DEFAULT_STATE_DIR: Final[Path] = Path("/var/lib/sshblock")
DEFAULT_DB_PATH: Final[Path] = DEFAULT_STATE_DIR / "sshblock.db"
DEFAULT_STATE_FILE: Final[Path] = DEFAULT_STATE_DIR / "tail_state.json"