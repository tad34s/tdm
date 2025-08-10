from pathlib import Path

import click

from tdm.print_to_user import error, success
from tdm.state import State


@click.command()
@click.option("--keep", "-k", is_flag=True, help="Keep files after removing symlinks")
def vacate(keep: bool) -> None:
    """Remove deployed symlinks"""
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return
    state.desymlink(keep)
    state.delete()

    # state.clean_app_dir()
    success(f"vacated the \033[3m{str(state.repo.relative_to(Path.home()))}\033[0m repo.")
