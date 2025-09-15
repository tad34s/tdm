import shutil
from pathlib import Path


def add_to_set_file(file: Path, entry: str) -> bool:
    entries = []
    if file.exists():
        with file.open("r") as f:
            entries = set(x.strip() for x in f.readlines())
    if entry in entries:
        return False
    with file.open("a") as f:
        f.write(entry + "\n")
    return True


def remove_from_set_file(file: Path, entry: str) -> bool:
    if not file.exists():
        return False
    with file.open("r") as f:
        entries = set(x.strip() for x in f.readlines())
    if entry not in entries:
        return False
    entries.remove(entry)
    if not entries:
        file.unlink()
    else:
        with file.open("w") as f:
            f.writelines(x + "\n" for x in entries)
    return True


def read_set_file(file: Path) -> set[str]:
    if not file.exists():
        return set()
    with file.open("r") as f:
        entries = set(x.strip() for x in f.readlines())
    return entries


def is_empty_dir(dir: Path) -> bool:
    has_next = next(dir.iterdir(), None)
    return has_next is None


def clean_parents(file: Path):
    """Deletes parents if they are empty."""
    curr_parent = file.parent
    while curr_parent.exists() and is_empty_dir(curr_parent):
        curr_parent.rmdir()
        curr_parent = curr_parent.parent


def delete(path: Path) -> None:
    if path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def copy(src: Path, dest: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dest)


def move(src: Path, dest: Path) -> None:
    shutil.move(src, dest)


def ensure_parents(path: Path) -> None:
    """Create all the parents of a file if they do not exist."""
    path.parent.mkdir(exist_ok=True, parents=True)


def copy_skip_present(src: Path, dest: Path) -> None:
    """Copy from src to dest.
    If the src or a child of the src is already at the destination we skip it (this part of destination is unchanged)
    """

    def recursively_copy(src_dir: Path, dest_dir: Path):
        for item in src_dir.iterdir():
            relative_path = item.relative_to(src_dir)
            target = dest_dir / relative_path
            if item.is_file():
                # Skip existing files
                if target.exists():
                    continue

                # Ensure parent directory exists
                target.parent.mkdir(parents=True, exist_ok=True)

                # Copy file with metadata
                shutil.copy2(item, target)
            else:
                recursively_copy(item, target)

    if not dest.exists():
        dest.parent.mkdir(exist_ok=True, parents=True)
        copy(src, dest)
    else:
        recursively_copy(src, dest)


def move_skip_present(src: Path, dest: Path) -> None:
    """Move from src to dest.
    If the src or a child of the src is already at the destination we skip it (this part of destination is unchanged) the src will be then deleted.
    """

    def recursively_move(src_dir: Path, dest_dir: Path):
        for item in src_dir.iterdir():
            relative_path = item.relative_to(src_dir)
            target = dest_dir / relative_path
            if item.is_file():
                if target.exists():
                    item.unlink()
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(item, target)
            else:
                recursively_move(item, target)

    if not dest.exists() or src.is_file():
        dest.parent.mkdir(exist_ok=True, parents=True)
        shutil.move(src, dest)
    else:
        recursively_move(src, dest)
        if src.exists():
            delete(src)


def remove_relative(absolute_path: Path, relative_suffix: Path):
    # Traverse up the number of times equal to the parts in the relative path
    base = absolute_path
    print(absolute_path, relative_suffix)
    parts = reversed(relative_suffix.parts)
    for part in parts:
        assert part == base.name, f"{part}!={base.name} part of the relative path does not match"
        base = base.parent
    return base


def symlink_item(item: Path, original_base: Path, new_base: Path) -> None:
    """Create new symlink in the new_base pointing to the item in the original_base.
    Will delete the path in the new base if exists.
    """
    relative_path = item.relative_to(original_base)
    target_path = new_base / relative_path
    if target_path.exists():
        if target_path.is_symlink() and target_path.readlink() == item:
            return
        delete(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.symlink_to(item, target_is_directory=item.is_dir())
