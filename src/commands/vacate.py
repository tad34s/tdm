from pathlib import Path

import click

from print_to_user import error
from state import State


def recursively_change_softlinks_to_hardlinks(
    curr_dir: Path,
    dotfiles_base: Path,
    symlink_location_base: Path,
) -> None:
    for item in curr_dir.iterdir():
        relative_path = item.relative_to(dotfiles_base)
        other_item = symlink_location_base / relative_path
        if other_item.is_symlink():
            og_item = other_item.readlink()
            other_item.unlink()
            other_item.hardlink_to(og_item)

        elif item.is_dir():
            recursively_change_softlinks_to_hardlinks(
                item, dotfiles_base, symlink_location_base
            )


@click.command()
@click.option("--keep", "-k", is_flag=True, help="Keep files after removing symlinks")
def vacate(keep: bool) -> None:
    """Remove deployed symlinks"""
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return
    if not keep:
        state.desymlink()
    else:
        recursively_change_softlinks_to_hardlinks(
            state.file_dir, state.file_dir, Path.home()
        )
