import shutil
from pathlib import Path

import click

from tdm.file_tree import create_tree, symlink_and_backup_tree
from tdm.print_to_user import error
from tdm.state import State
from tdm.symlink_utils import desymlink_dir, symlink_and_backup_item


def selectively_copy(real_dir: Path, state: State) -> None:
    for item in real_dir.iterdir():
        if any(x in str(item) for x in state.config.ignore):
            continue
        if item.is_dir():
            selectively_copy(item, state)
        else:
            relative_path = item.relative_to(Path.home())
            dest_dotfiles = state.file_dir / relative_path
            dest_dotfiles.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy(item, dest_dotfiles)


@click.command
@click.argument("path")
def add(path: str):
    """Add a directory or a file to tdm."""
    resource = Path(path).resolve()
    if not resource.exists():
        error("Resource does not exist.")

    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    relative_path = resource.relative_to(Path.home())
    dotfile_path = state.file_dir / relative_path

    if dotfile_path.exists():
        if (  # checking if it was added already
            resource.is_file()
            or any(  # meaning its parent or the resource itself was already added
                str(relative_path).startswith(x) for x in state.symlinked_dirs
            )
        ):
            error(
                "Already managing selected resource. Use the fork command to create a different version."
            )
            return

        # either adding a new dir, the children could be already added tho
        if resource.is_dir():
            desymlink_dir(
                dotfile_path,
                state.file_dir,
                Path.home(),
                state.get_app_data_dir() / state.BACKUP_DIR,
            )

    if resource.is_dir():
        state.add_symlinked_dir(str(relative_path))
        selectively_copy(resource, state)
        file_subtree = create_tree(
            state,
            state.file_dir / relative_path,
            state.symlinked_dirs,
        )
        symlink_and_backup_tree(file_subtree, state)

    else:
        dotfile_path.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy(resource, dotfile_path)
        symlink_and_backup_item(
            dotfile_path,
            state.file_dir,
            Path.home(),
            state.get_app_data_dir(create=True) / state.BACKUP_DIR,
        )
