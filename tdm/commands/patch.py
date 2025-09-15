from pathlib import Path
from shutil import copy

import click

from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_manager import SymlinkManager


def add_new_children(relative_path: Path, state: State):
    resource = Path.home() / relative_path
    if state.is_forked_by_current_profile(relative_path):
        dotfile = state.fork_dir / relative_path
    else:
        dotfile = state.file_dir / relative_path

    # copy
    if not dotfile.exists():
        dotfile.parent.mkdir(exist_ok=True, parents=True)
        if resource.is_dir():
            state.copy_dir_to_repo(resource)
        else:
            copy(resource, dotfile)
        return

    if resource.is_symlink():
        return

    if not resource.is_dir():
        return

    for item in resource.iterdir():
        if any(x in str(item) for x in state.config.ignore):
            continue
        add_new_children(item.relative_to(Path.home()), state)


@click.command
def patch():
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    symlink_manager = SymlinkManager(state, state.file_dir, backup_location=state.backup_location())
    for dir in state.added_dirs:
        if not (state.file_dir / dir).exists():
            state.remove_added_dir(dir)
            state.remove_backup(Path(dir))
            continue

        add_new_children(Path(dir), state)

    symlink_manager.patch()
    success("patched.")
