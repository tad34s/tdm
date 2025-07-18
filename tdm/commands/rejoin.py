from pathlib import Path

import click

from tdm.print_to_user import error
from tdm.state import State
from tdm.symlink_utils import desymlink_and_recover_item


@click.command
@click.argument("resource")
@click.option("--keep", "-k", is_flag=True, help="Replace base version with forked version.")
def rejoin(path: str, keep: bool):
    """Deletes the fork and replaces it witht the base configuration.
    If keep is on, it will replace the base with the forked instead. But will still delete the fact
    that the file is forked for this profile.
    """
    resource = Path(path).resolve()
    if not resource.exists():
        error("Resource does not exist.")

    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    # command ran inside the repo
    if state.repo in resource.parents:
        dotfile_path = resource
    else:
        relative_path = resource.relative_to(Path.home())
        dotfile_path = state.file_dir / relative_path
        if not dotfile_path.exists():
            error("Not managing selected resource.")
            return

    relative_path = dotfile_path.relative_to(state.file_dir)
    fork_file = state.fork_dir / relative_path

    if not fork_file.exists():
        error("Resource was not forked.")

    if keep:
        fork_file.replace(state.get_repo_data_dir() / state.BASE_BACKUP_DIR / relative_path)

    # stop fork
    desymlink_and_recover_item(
        dotfile_path, state.file_dir, state.get_repo_data_dir() / state.BASE_BACKUP_DIR
    )

    # delete fork
    if fork_file.exists():
        fork_file.unlink()
