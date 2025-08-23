from pathlib import Path

import click

from tdm.fs_utils import delete
from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_utils import desymlink_path


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

    if state.file_dir in resource.parents:
        relative_path = resource.relative_to(state.file_dir)
    elif state.fork_dir in resource.parents:
        relative_path = resource.relative_to(state.fork_dir)
    else:
        relative_path = resource.relative_to(Path.home())

    dotfile_path = state.file_dir / relative_path
    if not dotfile_path.exists():
        error("Not managing selected resource.")

    fork_path = state.fork_dir / relative_path

    if not fork_path.exists():
        error("Resource was not forked.")

    backup_location = state.fork_dir if keep else state.get_repo_data_dir() / state.FORK_BACKUP_DIR

    # stop fork
    desymlink_path(fork_path, state.fork_dir, state.file_dir, backup_location)
    if dotfile_path.is_dir():
        state.remove_forked_dir(str(relative_path))

    # delete fork
    # when keep is True, the backup location is fork dir, which results in moving the file from fork dir -> no longer exists
    if fork_path.exists():
        delete(fork_path)

    success(f"rejoined \033[3m{path}\033[0m.")
