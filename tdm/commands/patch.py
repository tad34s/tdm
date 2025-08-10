from pathlib import Path
from shutil import copy, rmtree

import click

from tdm.file_tree import create_tree, symlink_tree
from tdm.fs_utils import move
from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_utils import desymlink_dir


def add_new_children(relative_path: Path, state: State):
    resource = Path.home() / relative_path
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


def kickout_ignored(curr_src_dir: Path, state: State):
    for item in curr_src_dir.iterdir():
        if state.is_ignored(item):
            relative_path = item.relative_to(state.file_dir)
            target_path = Path.home() / relative_path
            target_path.parent.mkdir(exist_ok=True, parents=True)
            if target_path.is_dir():
                rmtree(target_path)
            move(item, target_path)
        if item.is_dir():
            kickout_ignored(item, state)


@click.command
def patch():
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    for dir in state.added_dirs:
        if not (state.file_dir / dir).exists():
            state.remove_added_dir(dir)
            state.remove_backup(Path(dir))
            continue

        add_new_children(Path(dir), state)

        desymlink_dir(
            state.file_dir / dir,
            state.file_dir,
            Path.home(),
        )

        kickout_ignored(state.file_dir / dir, state)

    file_subtree = create_tree(
        state,
        state.file_dir,
        state.added_dirs,
    )

    symlink_tree(file_subtree, state)

    success("patched.")
