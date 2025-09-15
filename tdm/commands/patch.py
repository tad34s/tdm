from pathlib import Path
from shutil import copy

import click

import tdm.tests.utils as ts
from tdm.file_tree import FileTree
from tdm.print_to_user import error, success
from tdm.state import State


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

    file_tree = FileTree(state, state.file_dir, backup_location=state.backup_location())
    print("stuff", ts.file_tree(Path.home()))
    for dir in state.added_dirs:
        if not (state.file_dir / dir).exists():
            state.remove_added_dir(dir)
            state.remove_backup(Path(dir))
            continue

        print("patching", Path(dir))
        add_new_children(Path(dir), state)

    file_tree.patch()
    success("patched.")
