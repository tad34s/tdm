# TODO: when forking a direcotry add it to forks/profile/path_todir/forked_dirs, check if it is already present
# check if the the file is already present

import shutil
from pathlib import Path

import click

from print_to_user import error
from state import State

# TODO: Check that a fork is not inside a forked directory.

# TODO: Maybe some other already forked stuff?


@click.command
@click.argument("resource")
@click.option("--profile", "-p", help="Fetch the new contents from the profile selected.")
@click.option(
    "--symlink", "-s", is_flag=True, help="Symlink instead of copying from profile selected."
)
def fork(path: str, profile: str | None, to_symlink: bool):
    resource = Path(path).resolve()
    if not resource.exists():
        error("Resource does not exist.")

    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    # command run inside the repo
    if state.repo in resource.parents:
        dotfile_path = resource
    else:
        relative_path = resource.relative_to(Path.home())
        dotfile_path = state.file_dir / relative_path
        if not dotfile_path.exists():
            error("Not managing selected resource.")
            return

    relative_path = dotfile_path.relative_to(state.file_dir)
    not_yet_forked = (state.fork_dir / relative_path).exists()

    # Prepare the forks dir
    # populate the forks/profile/../file correctly
    if to_symlink:  # populate with symlink
        if profile is None:
            error("Profile not specified.")
            return
        elif profile == state.profile:
            error("Cannot symlink to current profile.")

        new_link = state.fork_dir / relative_path
        if new_link.exists():
            new_link.unlink()
        new_link.symlink_to(
            state.repo / state.FORK_DIR_NAME / profile / relative_path,
            target_is_directory=(
                state.repo / state.FORK_DIR_NAME / profile / relative_path
            ).is_dir(),
        )
    else:
        if profile is None:  # use the current profile as source
            shutil.copytree(dotfile_path, state.fork_dir / relative_path)
        else:
            shutil.copytree(
                state.repo / state.FORK_DIR_NAME / profile / relative_path,
                state.fork_dir / relative_path,
            )

    # mark that the whole dir is forked
    if dotfile_path.is_dir() and not_yet_forked:
        forked_dirs_file = state.fork_dir / state.FORKED_DIRS_FILE
        with forked_dirs_file.open("a") as f:
            f.write(str(relative_path))

    # Apply the fork to file dir
    state.symlink_item(
        state.fork_dir / relative_path,
        state.fork_dir,
        state.file_dir,
        state.get_repo_data_dir(create=True) / state.BASE_BACKUP_DIR,
    )
