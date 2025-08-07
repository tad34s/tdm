from pathlib import Path

import click
from git import rmtree

from tdm.fs_utils import remove_from_set_file
from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_utils import desymlink_and_recover_item


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
    target_path = Path.home() / relative_path

    if not dotfile_path.exists():
        error("Selected resource not managed.")
        return

    backup = state.get_app_data_dir(create=True) / state.BACKUP_DIR / relative_path

    # desymlink
    if not keep:
        desymlink_and_recover_item(
            target_path, Path.home(), state.get_app_data_dir() / state.BACKUP_DIR
        )
    else:
        desymlink_and_recover_item(target_path, Path.home(), state.file_dir)

    if dotfile_path.is_dir():
        state.remove_added_dir(str(relative_path))

        # delete forks
        for fork_dir in (state.repo / state.FORK_DIR_NAME).iterdir():
            forked_item = fork_dir / relative_path
            if not forked_item.exists():
                continue

            forked_dirs_file = fork_dir / state.FORKED_DIRS_FILE
            remove_from_set_file(forked_dirs_file, str(relative_path))
            forked_item.unlink()

    else:
        # delete forks
        for fork_dir in (state.repo / state.FORK_DIR_NAME).iterdir():
            forked_item = fork_dir / relative_path
            if not forked_item.exists():
                continue
            forked_item.unlink()

    if dotfile_path.exists():
        if dotfile_path.is_dir():
            rmtree(dotfile_path)
        else:
            dotfile_path.unlink()

    success(f"removed \033[3m{path}\033[0m.")
