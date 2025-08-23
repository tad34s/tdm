from pathlib import Path

import click

import tdm.fs_utils as fs
from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_utils import desymlink_path


@click.command
@click.argument("path")
@click.option("--keep", "-k", is_flag=True, help="Replace the symlink with the dotfile specified")
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

    relative_path = state.get_relative_path(resource)
    dotfile_path = state.file_dir / relative_path

    if not state.is_managed(relative_path):
        error("Selected path not managed.")
        return

    if keep:
        backup_location = state.file_dir
    elif delete:
        backup_location = None
    else:
        backup_location = state.backup_location()

    # desymlink the symlinks deployed
    desymlink_path(dotfile_path, state.file_dir, Path.home(), backup_location)

    if dotfile_path.is_dir():
        state.remove_added_dir(str(relative_path))
        if state.is_forked(relative_path):
            state.remove_forked_dir(str(relative_path))
        else:  # children of the path might be forked
            for fork_dir in state.profile_fork_dirs:
                if (fork_dir / relative_path).exists():
                    state.remove_children_in_forked_dir(str(relative_path))
                    break

    state.delete_forks(relative_path)
    state.remove_backup(relative_path)
    if dotfile_path.exists():
        fs.delete(dotfile_path)

    success(f"removed \033[3m{path}\033[0m.")
