from pathlib import Path

import click

from tdm.print_to_user import error
from tdm.state import State


@click.command()
@click.argument("path")
@click.option("--message", "-m", default=None, help="Commit message")
def commit(path: Path, message: str) -> None:
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    state.unapply_forks()

    # git commit ...

    state.apply_forks()
