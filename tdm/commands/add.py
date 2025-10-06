import shutil
from pathlib import Path

import click

from tdm.print_to_user import error, success, warning
from tdm.state import State
from tdm.symlink_manager import SymlinkManager


@click.command
@click.argument("path")
def add(path: str):
    """Add a directory or a file to tdm."""
    resource = Path(path).resolve()
    if not resource.exists():
        error("Resource does not exist.")

    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    relative_path = state.get_relative_path(resource)
    dotfile_path = state.file_dir / relative_path

    if state.is_managed(relative_path):
        error(
            "Already managing selected resource. Use the fork command to create a different version."
        )

    if state.is_ignored(relative_path):
        error("Selected path is ignored by the current configuration.")

    if state.is_excluded(relative_path):
        warning(
            "Selected path is excluded by the current profile. You can add it but to start using it, you will have to switch profiles.",
            ask_continue=True,
        )

    symlink_manager = SymlinkManager.current(state, backup_location=state.backup_location())

    if resource.is_dir():
        if dotfile_path.exists():
            # adding a parent of some already added dotfile
            # we should first desymlink the children
            # desymlink_dir(dotfile_path, state.file_dir, Path.home())
            # then remove that the children were added
            state.remove_children_in_added_dir(str(relative_path))

        state.add_added_dir(str(relative_path))
        state.copy_dir_to_repo(resource)
    else:
        dotfile_path.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy(resource, dotfile_path)

    symlink_manager.patch()

    success(f"added \033[3m{relative_path}\033[0m.")
