from dataclasses import dataclass
from pathlib import Path

import click

from tdm.print_to_user import error
from tdm.state import State
from tdm.symlink_manager import SymlinkManager


@dataclass
class Vertex:
    key: Path
    children: list["Vertex"]


def item_name(path: Path):
    item_name = path.name
    if path.is_symlink():
        if path.readlink().exists():
            item_name = "\033[36m" + item_name + f" -> {path.readlink()}" + "\033[0m"
        else:
            item_name = "\x1b[31m" + item_name + f" -> {path.readlink()}" + "\033[0m"
    elif path.is_dir():
        item_name = "\033[34m" + item_name + "/" + "\033[0m"

    return item_name


def file_tree(path: Path, prefix: str = "", old_indent="", indent="   ") -> str:
    """Generate a string representation of the directory tree"""
    output = []
    item_text = f"{old_indent}{prefix}{item_name(path)}"
    output.append(item_text)

    if path.is_dir() and ".git" != path.name:
        children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        count = len(children)
        if count > 4:
            child_output = file_tree(children[0], "├── ", indent, indent + "|  ")
            output.append(child_output)
            output += [f"{indent}."] * 3
            child_output = file_tree(children[-1], "└── ", indent, indent + "   ")
            output.append(child_output)

        else:
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


def file_tree_vertex(vertex: Vertex, prefix: str = "", old_indent="", indent="   ") -> str:
    """Generate a string representation of the directory tree"""
    output = []
    path = Path.home() / vertex.key
    if path.is_symlink():
        output.append(file_tree(path, prefix, old_indent, indent))
        return "\n".join(output)

    item_text = f"{old_indent}{prefix}{item_name(path)}"
    output.append(item_text)

    if vertex.children:
        count = len(vertex.children)
        for i, child in enumerate(vertex.children):
            is_last = i == count - 1
            if is_last:
                new_prefix = "└── "
                new_indent = indent + "   "
            else:
                new_prefix = "├── "
                new_indent = indent + "|  "

            child_output = file_tree_vertex(child, new_prefix, indent, new_indent)
            output.append(child_output)

    return "\n".join(output)


@click.command
def tree():
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    symlink_manager = SymlinkManager(state, state.file_dir, backup_location=state.backup_location())

    nodes = [x for x in symlink_manager.symlinked_nodes_iter(state, Path.home(), None)]

    root = Vertex(key=Path.home(), children=[])

    for node in nodes:
        current = root
        parents = list(reversed(node.relative_path.parents)) + [node.relative_path]
        for parent in parents[1:]:
            for child in current.children:
                if child.key == parent:
                    current = child
                    break
            else:
                new_child = Vertex(key=parent, children=[])
                current.children.append(new_child)
                current = new_child

    print(file_tree_vertex(root))
