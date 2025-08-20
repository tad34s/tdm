from pathlib import Path

import click

from tdm.fs_utils import delete
from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_utils import desymlink_path


@click.command
@click.argument("path")
@click.option("--keep", "-k", is_flag=True, help="Keep dotfile")
def rm(path: str, keep: bool):
    """Remove a file or a directory from tdm."""
    resource = Path(path).resolve()
    if not resource.exists():
        error("Resource does not exist.")

    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    relative_path = state.get_relative_path(resource)
    dotfile_path = state.file_dir / relative_path

    if not dotfile_path.exists():
        error("Selected resource not managed.")
        return

    backup_location = state.file_dir if keep else state.backup_location()

    # desymlink
    desymlink_path(dotfile_path, state.file_dir, Path.home(), backup_location)

    if dotfile_path.is_dir():
        state.remove_added_dir(str(relative_path))

        # delete forks
        for fork_dir in (state.repo / state.FORK_DIR_NAME).iterdir():
            forked_item = fork_dir / relative_path
            if not forked_item.exists():
                continue

            if str(relative_path) in state.forked_dirs:
                state.remove_forked_dir(str(relative_path))
            delete(forked_item)

    else:
        # delete forks
        for fork_dir in (state.repo / state.FORK_DIR_NAME).iterdir():
            forked_item = fork_dir / relative_path
            if not forked_item.exists():
                continue
            forked_item.unlink()

    if dotfile_path.exists():
        delete(dotfile_path)

    success(f"removed \033[3m{path}\033[0m.")
