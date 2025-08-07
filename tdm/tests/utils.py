import traceback
from pathlib import Path
from types import TracebackType

from click.testing import Result


def file_tree(path: Path, prefix: str = "", old_indent="", indent="   ") -> str:
    """Generate a string representation of the directory tree"""
    output = []
    item_name = path.name
    if path.is_symlink():
        item_name = "\033[36m" + item_name + f" -> {path.readlink()}" + "\033[0m"
    elif path.is_dir():
        item_name = "\033[34m" + item_name + "/" + "\033[0m"

    item_text = f"{old_indent}{prefix}{item_name}"
    output.append(item_text)

    if path.is_dir() and ".git" != path.name:
        children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        count = len(children)
        for i, child in enumerate(children):
            is_last = i == count - 1
            if is_last:
                new_prefix = "└── "
                new_indent = indent + "   "
            else:
                new_prefix = "├── "
                new_indent = indent + "|  "

            child_output = file_tree(child, new_prefix, indent, new_indent)
            output.append(child_output)

    return "\n".join(output)


def assert_result(result: Result, command_name: str, home: Path | None = None):
    print(f"StdOut:\n{result.stdout}")
    print(f"StdErr:\n{result.stderr}")
    print(f"Exception:{result.exception}")
    tracebakc_ig: TracebackType = result.exc_info[2]
    print("Traceback:")
    print(traceback.print_tb(tracebakc_ig))
    print("-------")
    if home:
        print(f"Tree after {command_name}: \n", file_tree(home))
    assert result.exit_code == 0, f"{command_name} failed\n"


def check_files(files: list[tuple[Path, str]], home: Path):
    for file, content in files:
        real_file = home / file
        assert real_file.read_text() == content
