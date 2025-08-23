from os import error
from pathlib import Path

import tdm.fs_utils as fs


def symlink_item(item: Path, original_base: Path, new_base: Path) -> None:
    """Create new symlink in the new_base pointing to the item in the original_base.
    Will delete the path in the new base if exists.
    """
    relative_path = item.relative_to(original_base)
    target_path = new_base / relative_path
    if target_path.exists():
        if target_path.is_symlink() and target_path.readlink() == item:
            return
        fs.delete(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.symlink_to(item, target_is_directory=item.is_dir())


def symlink_and_backup_item(
    item: Path, original_base: Path, new_base: Path, backup_location: Path
) -> None:
    relative_path = item.relative_to(original_base)
    target_path = new_base / relative_path
    if target_path.exists():
        if target_path.is_symlink():
            if target_path.readlink() == item:
                return
            target_path.unlink()
        else:
            backup_dest = backup_location / relative_path
            backup_dest.parent.mkdir(exist_ok=True, parents=True)
            fs.move_skip_present(target_path, backup_dest)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.symlink_to(item, target_is_directory=item.is_dir())


def desymlink_path(
    src_path: Path,
    src_path_base: Path,
    target_path_base: Path,
    backup_location: Path | None = None,
) -> None:
    """
    Desymlink the src path, if it has children also desymlink them.
    Desymlinking a path means:
    1. Find the symlink location, by swapping src_dir_base with target_base
    2. If there exists a symlink it will delete it. If backup path is provided it will replace it with the backup instead.
    """

    if not src_path.exists():
        error("Tried to desymlinked a not managed file. Aborting...")

    relative_path = src_path.relative_to(src_path_base)
    target_path = target_path_base / relative_path
    if not target_path.exists():
        return

    if target_path.is_symlink():
        target_path.unlink()
    elif target_path.is_dir():
        desymlink_dir(src_path, src_path_base, target_path_base, backup_location)

    if backup_location is not None:
        backup_path = backup_location / relative_path
        if backup_path.exists():
            fs.move(backup_path, target_path)
        fs.clean_parents(backup_path)


def desymlink_dir(
    src_dir: Path,
    src_dir_base: Path,
    target_location_base: Path,
    backup_location: Path | None = None,
    copy: bool = False,
) -> None:
    """Go through the src dir. For each entry:
    1. Find the symlink location, by swapping src_dir_base with target_base
    2. If there exists a symlink it will delete it. If backup path is provided it will replace it with the backup instead.

    copy: If true will copy from backup location to target instead of move.
    """
    relative_path = src_dir.relative_to(src_dir_base)
    target = target_location_base / relative_path
    backup_fn = fs.copy if copy else fs.move
    if target.is_symlink():
        target.unlink()
    for item in src_dir.iterdir():
        relative_path = item.relative_to(src_dir_base)
        target = target_location_base / relative_path
        if target.is_symlink():
            if backup_location is not None:
                target.unlink()
                backup_path = backup_location / relative_path
                if backup_path.exists():
                    backup_fn(backup_path, target)
                    fs.clean_parents(backup_path)
            else:
                target.unlink()

        elif item.is_dir():
            desymlink_dir(item, src_dir_base, target_location_base, backup_location, copy)


def desymlink_fork(target_dotfile: Path, base_path: Path, backup_location: Path):
    relative_path = target_dotfile.relative_to(base_path)
    backup_path = backup_location / relative_path
    if target_dotfile.is_symlink():
        target_dotfile.unlink()
    if backup_path.exists():
        fs.move(backup_path, target_dotfile)
        fs.clean_parents(backup_path)
