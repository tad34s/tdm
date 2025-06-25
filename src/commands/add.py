from pathlib import Path

import click

from print_to_user import error
from state import State


@click.command
@click.argument("resource")
def add(path: str):
    resource = Path(path).resolve()
    if not resource.exists():
        error("Resource does not exist.")

    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    relative_path = resource.relative_to(Path.home())
    dotfile_path = state.file_dir / relative_path

    if dotfile_path.exists():
        error(
            "Already managing selected resource. Use the fork command to create a different version."
        )
        return

    if resource.is_dir():
        symlinked_dirs_file = state.get_repo_data_dir(create=True) / State.SYMLINKED_DIRS
        with symlinked_dirs_file.open("a") as f:
            f.write(str(relative_path))

    resource = resource.replace(dotfile_path)
    state.symlink_item(
        resource,
        state.file_dir,
        Path.home(),
        state.get_app_data_dir(create=True) / state.BACKUP_DIR,
    )
