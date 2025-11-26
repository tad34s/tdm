from pathlib import Path

import click

from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_manager import SymlinkManager


@click.command()
@click.option("--keep", "-k", is_flag=True, help="Keep files after removing symlinks")
def vacate(keep: bool) -> None:
    """Remove deployed symlinks and restore state before tdm."""
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return
    symlink_manager = SymlinkManager.current(state, backup_location=state.backup_location())
    if keep:
        symlink_manager.desymlink_keep()
    else:
        symlink_manager.desymlink(use_backup=True)

    state.clean_app_dir()
    success(f"vacated the \033[3m{str(state.repo.relative_to(Path.home()))}\033[0m repo.")
