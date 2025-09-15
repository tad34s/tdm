import subprocess
import sys

import click

from tdm.file_tree import FileTree
from tdm.print_to_user import error, success
from tdm.state import State


@click.command
def update():
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    file_tree = FileTree(state, state.file_dir, backup_location=state.backup_location())

    try:
        # Execute git with captured arguments
        result = subprocess.run(["git", "pull"], check=False, cwd=state.repo)
    except Exception as e:
        file_tree.resymlink()
        error(f"Failed to pull from git: {e}")
        return

    file_tree.resymlink()

    # Propagate git's exit code
    sys.exit(result.returncode)
    success("dotfiles are up to date.")
