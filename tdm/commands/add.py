from pathlib import Path

import click

from tdm import file_tree
from tdm.print_to_user import error
from tdm.state import State


def selectively_move(real_dir: Path, state: State) -> None:
    for item in real_dir.iterdir():
        if any(x in str(item) for x in state.config.ignore):
            continue
        if item.is_dir():
            selectively_move(item, state)
        else:
            relative_path = item.relative_to(Path.home())
            dest_replace = state.file_dir / relative_path
            dest_replace.parent.mkdir(exist_ok=True, parents=True)
            item.replace(dest_replace)


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
        error(
            "Already managing selected resource. Use the fork command to create a different version."
        )
        return

    if resource.is_dir():
        state.add_symlinked_dir(str(relative_path))
        selectively_move(resource, state)
        file_subtree = file_tree.create_tree(
            state,
            state.file_dir / relative_path,
            state.symlink_dirs,
        )
        file_tree.symlink(file_subtree, state)

    else:
        dotfile_path.parent.mkdir(exist_ok=True, parents=True)
        resource = resource.rename(dotfile_path)
        state.symlink_and_backup_item(
            resource,
            state.file_dir,
            Path.home(),
            state.get_app_data_dir(create=True) / state.BACKUP_DIR,
        )
