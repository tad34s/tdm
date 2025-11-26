from pathlib import Path

import click

import tdm.fs_utils as fs
from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_manager import SymlinkManager


@click.command
@click.argument("path")
@click.option("--keep", "-k", is_flag=True, help="Replace the symlink with the current dotfile")
@click.option("--delete", "-d", is_flag=True, help="Delete the symlink and the dotfile")
def rm(path: str, keep: bool, delete: bool):
    """Remove a file or a directory from tdm. Replaces it with the backed up version"""
    resource = Path(path).resolve()
    if not resource.exists():
        error("Path does not exist.")

    if keep and delete:
        error("--keep and --delete are mutually exclusive options.")

    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    symlink_manager = SymlinkManager.current(state, backup_location=state.backup_location())
    relative_path = state.get_relative_path(resource)

    if not state.is_managed(relative_path):
        error("Selected path not managed.")
        return

    base_dotfile_path = state.file_dir / relative_path

    if base_dotfile_path.is_dir():
        state.remove_added_dir(str(relative_path))
        if state.is_forked(relative_path):
            state.remove_forked_dir(str(relative_path))
        else:  # children of the path might be forked
            for fork_dir in state.profile_fork_dirs:
                if (fork_dir / relative_path).exists():
                    state.remove_children_in_forked_dir(str(relative_path))
                    break

    node = symlink_manager.get_node(relative_path)
    if node is None:
        nodes = symlink_manager.get_children(relative_path)
        for child in nodes:
            if keep:
                symlink_manager.remove_node_keep(child)
            elif delete:
                symlink_manager.remove_node_delete(child)
            else:
                symlink_manager.remove_node_backup(child)
    if node is not None:  # if node is None the item is not symlinked at all
        if keep:
            symlink_manager.remove_node_keep(node)
        elif delete:
            symlink_manager.remove_node_delete(node)
        else:
            symlink_manager.remove_node_backup(node)

    if base_dotfile_path.exists():  # if keep we move the file therefore it does not exists
        fs.delete(base_dotfile_path)
    state.delete_forks(relative_path)
    state.remove_backup(relative_path)

    symlink_manager.patch()
    success(f"removed \033[3m{relative_path}\033[0m.")
