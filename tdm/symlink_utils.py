import shutil
from pathlib import Path

from tdm.fs_utils import clean_parents


def symlink_item(item: Path, original_base: Path, new_base: Path) -> None:
    relative_path = item.relative_to(original_base)
    target_path = new_base / relative_path
    if target_path.exists():
        if target_path.is_dir():
            shutil.rmtree(target_path)
        else:
            target_path.unlink()
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
            target_path.replace(backup_dest)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.symlink_to(item, target_is_directory=item.is_dir())


def desymlink_and_recover_item(item: Path, base_path: Path, backup_location: Path) -> None:
    relative_path = item.relative_to(base_path)
    backup_path = backup_location / relative_path
    item.unlink()
    if backup_path.exists():
        backup_path.replace(item)

    clean_parents(backup_path)


def desymlink_dir(
    src_dir: Path,
    src_dir_base: Path,
    target_location_base: Path,
    backup_location: Path | None = None,
) -> None:
    relative_path = src_dir.relative_to(src_dir_base)
    target = target_location_base / relative_path
    if target.is_symlink():
        target.unlink()
    for item in src_dir.iterdir():
        relative_path = item.relative_to(src_dir_base)
        target = target_location_base / relative_path
        if target.is_symlink():
            if backup_location is not None:
                desymlink_and_recover_item(
                    target,
                    target_location_base,
                    backup_location,
                )
            else:
                target.unlink()

        elif item.is_dir():
            desymlink_dir(item, src_dir_base, target_location_base, backup_location)
