from pathlib import Path

import click

from print_to_user import error
from state import State


@click.command
@click.argument("resource")
def forget(path: str):
    resource = Path(path).resolve()
    if not resource.exists():
        error("Resource does not exist.")

    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    if state.repo in resource.parents:
        dotfile_path = resource
    else:
        relative_path = resource.relative_to(Path.home())
        dotfile_path = state.file_dir / relative_path
        if not dotfile_path.exists():
            error("Not managing selected resource.")
            return

    relative_path = dotfile_path.relative_to(state.file_dir)

    if not dotfile_path.exists():
        error("Selected resource not managed.")
        return

    # update symlink dir
    if resource.is_dir():
        forked_dirs_file = state.get_repo_data_dir(create=True) / state.SYMLINKED_DIRS
        with forked_dirs_file.open("r") as f:
            forked_dirs = set(f.readlines())
        forked_dirs.remove(str(relative_path))
        with forked_dirs_file.open("w") as f:
            f.writelines(forked_dirs)

    # desymlink
    (dotfile_path.resolve()).replace(Path.home() / relative_path)

    # delete backup
    backup = state.get_app_data_dir(create=True) / state.BACKUP_DIR / relative_path
    if backup.exists():
        backup.unlink()

    # delete all forks
    for fork_dir in (state.repo / state.FORK_DIR_NAME).iterdir():
        fork_object = fork_dir / relative_path
        if fork_object.is_dir():
            forked_dirs_file = state.fork_dir / state.FORKED_DIRS_FILE
            with forked_dirs_file.open("r") as f:
                forked_dirs = set(f.readlines())
            forked_dirs.remove(str(relative_path))
            with forked_dirs_file.open("w") as f:
                f.writelines(forked_dirs)

        if fork_object.exists():
            fork_object.unlink()
