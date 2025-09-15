from pathlib import Path

import click

import tdm.fs_utils as fs
from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_manager import SymlinkManager


@click.command
@click.argument("path")
@click.option("--keep", "-k", is_flag=True, help="Replace base version with forked version.")
def rejoin(path: str, keep: bool):
    """Deletes the fork and replaces it witht the base configuration.
    If keep is on, it will replace the base with the forked instead. But will still delete the fact that the file is forked for this profile.
    """
    # We do not maintain information on the forked files.
    # -> If a parent of a file is forked we forget that the forked of the file took place.
    #  - meaning that if we rejoin the parent, the child will no longer be forked

    resource = Path(path).resolve()
    if not resource.exists():
        error("Resource does not exist.")

    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    symlink_manager = SymlinkManager(state, state.file_dir, backup_location=state.backup_location())

    relative_path = state.get_relative_path(resource)

    dotfile_path = state.file_dir / relative_path
    if not dotfile_path.exists():
        error("Not managing selected resource.")

    fork_path = state.fork_dir / relative_path

    if not fork_path.exists():
        error("Resource was not forked.")

    if dotfile_path.is_dir():
        state.remove_forked_dir(str(relative_path))

    # stop fork
    if keep:
        fs.move(fork_path, dotfile_path)
        fs.clean_parents(fork_path)
    else:
        fs.delete(fork_path)
        fs.clean_parents(fork_path)

    symlink_manager.patch()

    success(f"rejoined \033[3m{relative_path}\033[0m.")
