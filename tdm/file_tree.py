from dataclasses import dataclass
from pathlib import Path

from tdm.state import State


@dataclass
class TreeNode:
    path: Path
    symlink: bool
    children: list["TreeNode"]


def create_tree(
    state: State,
    curr_src_dir: Path,
    symlink_dirs: set[str],
    in_symlink_dir: bool = False,
) -> TreeNode:
    relative_path = curr_src_dir.relative_to(state.file_dir)
    should_symlink_all = in_symlink_dir or str(relative_path) in symlink_dirs
    could_symlink_all = should_symlink_all

    children: list[TreeNode] = []

    for item in curr_src_dir.iterdir():
        # excluding
        if any(x in str(item) for x in state.config.exclude):
            could_symlink_all = False  # cannot symlink whole dir
            continue

        if item.is_file(follow_symlinks=True):  # can always symlink a simple file
            children.append(TreeNode(item, True, []))

        elif item.is_dir(follow_symlinks=True):
            new_child = create_tree(state, item, symlink_dirs, should_symlink_all)
            if not new_child.symlink:  # check whether we could symlink whole child
                could_symlink_all = False
            children.append(new_child)

    # the corresponding dir in real home
    corresponding_dir = Path.home() / relative_path

    # check if we can really replace the whole corresponding dir
    if corresponding_dir.exists():
        for item in corresponding_dir.iterdir():
            if any(x in str(item) for x in state.config.ignore):
                could_symlink_all = False
                break

    return TreeNode(curr_src_dir, could_symlink_all, children)


def symlink(root: TreeNode, state: State) -> None:
    queue = [root]
    while queue:
        curr = queue.pop(0)
        if curr.path.is_file() or (curr.path.is_dir() and curr.symlink):
            State.symlink_item(
                curr.path,
                state.file_dir,
                Path.home(),
            )
        else:
            for child in curr.children:
                queue.append(child)


def symlink_and_backup(root: TreeNode, state: State) -> None:
    # NOTE: Traversing using BFS, the graph is a directed tree, so marking visited is not needed
    queue = [root]
    while queue:
        curr = queue.pop(0)
        if curr.path.is_file() or (curr.path.is_dir() and curr.symlink):
            State.symlink_and_backup_item(
                curr.path,
                state.file_dir,
                Path.home(),
                state.get_app_data_dir(create=True) / state.BACKUP_DIR,
            )
        else:
            for child in curr.children:
                queue.append(child)
