import shutil
from pathlib import Path

import click

from tdm.print_to_user import error, success
from tdm.state import State


def recursively_replace_links(
    src_dir: Path,
    dotfiles_base: Path,
    symlink_location_base: Path,
) -> None:
    for item in src_dir.iterdir():
        relative_path = item.relative_to(dotfiles_base)
        other_item = symlink_location_base / relative_path
        if item.is_dir():
            recursively_replace_links(item, dotfiles_base, symlink_location_base)
        elif other_item.is_symlink():
            og_item = other_item.readlink()
            other_item.unlink()
            shutil.copy(og_item, other_item)


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
        recursively_replace_links(state.file_dir, state.file_dir, Path.home())
    state.delete()

    # state.clean_app_dir()
    success(f"vacated the \033[3m{str(state.repo.relative_to(Path.home()))}\033[0m repo.")
