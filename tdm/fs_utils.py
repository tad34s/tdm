from pathlib import Path


def add_to_set_file(file: Path, entry: str) -> bool:
    entries = []
    if file.exists():
        with file.open("r") as f:
            entries = set(f.readlines())
    if entry in entries:
        return False
    with file.open("a") as f:
        f.write(entry + "\n")
    return True


def remove_from_set_file(file: Path, entry: str) -> bool:
    if not file.exists():
        return False
    with file.open("r") as f:
        entries = set(f.readlines())
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
