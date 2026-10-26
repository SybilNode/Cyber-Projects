"""Typer CLI entrypoint. Real commands are added in Phase 11."""

import typer

from sshblock import __version__

app = typer.Typer(
    help="SSH brute force detector (educational).",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """SSH brute force detector (educational)."""


@app.command()
def version() -> None:
    """Print the installed version."""
    typer.echo(f"sshblock {__version__}")