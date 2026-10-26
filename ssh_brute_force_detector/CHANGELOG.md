# Build Log

A running record of what was built, why, and what changed from the original plan.

## Phase 1: Scaffolding

**Files created**
- `pyproject.toml`: package metadata, dependencies, `sshblock` console script
- `src/sshblock/__init__.py`: package marker and `__version__`
- `src/sshblock/exceptions.py`: `SSHBlockError` base with `ConfigError`,
  `LogParseError`, `FirewallError`, `UnsafeBlockError`
- `src/sshblock/constants.py`: default log paths, thresholds (5/10/20 per 600s),
  block TTL, firewall chain name, circuit breaker limit, persistence paths
- `src/sshblock/main.py`: placeholder Typer app with `version` command
- `tests/test_exceptions.py`: verifies the exception hierarchy

**Decisions and deviations from the roadmap**
- Python 3.11+ required (`StrEnum`, `tomllib`).
- Dropped the `[email]`/`[slack]` extras: both use the standard library.
- Moved pytest/ruff/mypy to a `dev` extra; runtime deps are only typer and rich.
- Used the `src/` layout so tests run against the installed package.

**Verified by**
- `pip install -e ".[dev]"` succeeds
- `sshblock --help` and `sshblock version` run
- `pytest` passes