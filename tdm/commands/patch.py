# TODO: Refactor with add
# - copy + symlinking
import shutil
from pathlib import Path

import click

from tdm.commands.add import selectively_copy
from tdm.file_tree import create_tree, symlink_and_backup_tree
from tdm.print_to_user import error, success
from tdm.state import State


def add_new_children(relative_path: Path, state: State):
    resource = Path.home() / relative_path
    dotfile = state.file_dir / relative_path

    # copy
    if not dotfile.exists():
        dotfile.parent.mkdir(exist_ok=True, parents=True)
        if resource.is_dir():
            selectively_copy(resource, state)
        else:
            shutil.copy(resource, dotfile)
        return

    if resource.is_symlink():
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

    for dir in state.added_dirs:
        add_new_children(Path(dir), state)

    file_subtree = create_tree(
        state,
        state.file_dir,
        state.added_dirs,
    )
    symlink_and_backup_tree(file_subtree, state)
    success("patched.")
