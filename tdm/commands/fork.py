from pathlib import Path

import click

from tdm.fs_utils import copy_skip_present, delete
from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_utils import symlink_and_backup_item

# TODO: Check that a fork is not inside a forked directory.

# TODO: Maybe some other already forked stuff?

# TODO: Inside the forked directory is a symlinked fork


def was_forked(state: State, relative_path: Path) -> bool:
    # meaning its parent or the resource itself was already added
    if relative_path.is_file() and (state.fork_dir / relative_path).exists():
        return True
    if any(str(relative_path).startswith(x) for x in state.forked_dirs):
        return True

    return False


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

    if state.fork_dir in resource.parents:
        relative_path = resource.relative_to(state.fork_dir)
    elif state.file_dir in resource.parents:
        relative_path = resource.relative_to(state.file_dir)
    else:
        relative_path = resource.relative_to(Path.home())
    dotfile_path = state.file_dir / relative_path
    not_yet_forked = not was_forked(state, relative_path)

    if not dotfile_path.exists():
        error("Not managing selected resource.")

    if (
        profile is not None
        and not (state.repo / state.FORK_DIR_NAME / profile / relative_path).exists()
    ):
        error("The profile specified did not fork the selected path.")
    # Prepare the forks dir
    # populate the forks/profile/../file correctly
    if symlink:  # populate with symlink
        if profile is None:
            error("Profile not specified.")
            return
        elif profile == state.profile:
            error("Cannot symlink to current profile.")

        new_link = state.fork_dir / relative_path
        if new_link.exists():
            delete(new_link)
        new_link.parent.mkdir(exist_ok=True, parents=True)
        new_link.symlink_to(
            state.repo / state.FORK_DIR_NAME / profile / relative_path,
            target_is_directory=(
                state.repo / state.FORK_DIR_NAME / profile / relative_path
            ).is_dir(),
        )
    else:
        if profile is None:  # use the current profile as source
            file_in_fork_dir = state.fork_dir / relative_path
        else:
            file_in_fork_dir = state.repo / state.FORK_DIR_NAME / profile / relative_path

        file_in_fork_dir.parent.mkdir(exist_ok=True, parents=True)
        # copy keeping in mind already existing forks
        copy_skip_present(dotfile_path, file_in_fork_dir)

    # mark that the whole dir is forked
    if dotfile_path.is_dir() and not_yet_forked:
        state.add_forked_dir(str(relative_path))

    # Apply the fork to file dir
    symlink_and_backup_item(
        state.fork_dir / relative_path,
        state.fork_dir,
        state.file_dir,
        state.fork_backup_location(create=True),
    )

    success(f"forked \033[3m{path}\033[0m.")
