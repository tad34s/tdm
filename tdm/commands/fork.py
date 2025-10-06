from pathlib import Path

import click

import tdm.fs_utils as fs
from tdm.print_to_user import error, success, warning
from tdm.state import State
from tdm.symlink_manager import SymlinkManager


def has_symlink_in_relative_path(base_path, relative_path):
    """
    Check if any directory in the relative_path (when combined with base_path)
    is a symbolic link.

    Args:
        base_path (Path): The base directory path
        relative_path (Path): The relative path to check

    Returns:
        bool: True if any directory in the path contains a symlink, False otherwise
    """
    current_path = base_path
    for part in relative_path.parts:
        current_path = current_path / part
        if current_path.is_symlink():
            return True
    return False


def get_the_other_fork(state: State, profile: str) -> Path:
    if profile == state.BASE_PROFILE:
        origin_fork_dir = state.file_dir
    else:
        origin_fork_dir = state.fork_dir_profile(profile)

    return origin_fork_dir


@click.command
@click.argument("path")
@click.option(
    "--profile", "-p", default=None, help="Fetch the new contents from the profile selected."
)
@click.option(
    "--symlink",
    "-s",
    is_flag=True,
    default=False,
    help="Symlink instead of copying from profile selected.",
)
def fork(path: str, profile: str | None, symlink: bool = False):
    """Create a specific version of the resource selected for the current profile."""
    resource = Path(path).resolve()
    if not resource.exists():
        error("Resource does not exist.")

    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    if state.profile == state.BASE_PROFILE:
        error(
            "Cannot fork in the base profile. To be able to fork, create a new profile in the \033[3mconfig.toml\033[0m. file, and switch to it with the use command."
        )
        return

    symlink_manager = SymlinkManager.current(state, backup_location=state.backup_location())

    relative_path = state.get_relative_path(resource)
    dotfile_path = state.file_dir / relative_path
    not_yet_forked = not state.is_forked_by_current_profile(relative_path)

    # * First hangle warning and errors *
    if not state.is_managed(relative_path):
        error("Not managing selected resource.")

    if profile is None and symlink:
        error("No profile specified while passing the --symlink option.")

    dest_path = state.fork_dir / relative_path
    not_forked_but_child_is = dotfile_path.is_dir() and not_yet_forked and dest_path.exists()

    if symlink and has_symlink_in_relative_path(state.fork_dir, relative_path):
        error("Symlink was already used on a parent fork of this path.")

    if profile and profile == state.profile:
        error("The profile specified is the current active profile.")

    if not_forked_but_child_is:
        warning("You are forking a parent of an already made fork.", ask_continue=True)

    if profile:
        path_in_origin_fork_dir = state.fork_dir_profile(profile) / relative_path
        if not path_in_origin_fork_dir.exists():
            error("The profile specified did not fork the selected path.")

        if dest_path.exists():
            warning("You will overwrite the current fork for this profile.", ask_continue=True)
    else:
        if state.is_forked_by_current_profile(relative_path):
            error("The path specified is already forked.")

    # * Now do the actions *
    if not_forked_but_child_is:
        state.remove_children_in_forked_dir(str(relative_path))

    if profile:
        origin_fork_dir = state.fork_dir_profile(profile)
        path_in_origin_fork_dir = origin_fork_dir / relative_path
        if symlink:
            fs.symlink_item(path_in_origin_fork_dir, origin_fork_dir, state.fork_dir)
        else:
            dest_path.parent.mkdir(exist_ok=True, parents=True)
            # replacing original fork
            fs.copy(path_in_origin_fork_dir, dest_path)
    else:
        dest_path.parent.mkdir(exist_ok=True, parents=True)
        fs.copy_skip_present(state.file_dir / relative_path, dest_path)

    # mark that the whole dir is forked
    if dotfile_path.is_dir() and not_yet_forked:
        state.add_forked_dir(str(relative_path))

    # Apply the fork to file dir
    symlink_manager.patch()

    success(f"forked \033[3m{relative_path}\033[0m.")
