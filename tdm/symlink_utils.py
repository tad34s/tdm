import shutil
from pathlib import Path


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
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()
        else:
            backup_dest = backup_location / relative_path
            backup_dest.parent.mkdir(exist_ok=True, parents=True)
            target_path.replace(backup_dest)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.symlink_to(item, target_is_directory=item.is_dir())


def desymlink_and_recover_item(item: Path, base_path: Path, backup_location: Path) -> None:
    relative_path = item.relative_to(base_path)
    target_path = backup_location / relative_path
    if target_path.exists():
        item.unlink()
        target_path.replace(item)
    else:
        item.unlink()


def desymlink_dir(
    src_dir: Path,
    src_dir_base: Path,
    symlink_location_base: Path,
    backup_location: Path | None = None,
) -> None:
    for item in src_dir.iterdir():
        relative_path = item.relative_to(src_dir_base)
        target = symlink_location_base / relative_path
        if target.is_symlink():
            if backup_location is not None:
                desymlink_and_recover_item(
                    target,
                    symlink_location_base,
                    backup_location,
                )
            else:
                target.unlink()

        elif item.is_dir():
            desymlink_dir(item, src_dir_base, symlink_location_base, backup_location)
