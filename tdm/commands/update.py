import subprocess
import sys

import click

from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_manager import SymlinkManager


@click.command
def update():
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    symlink_manager = SymlinkManager.current(state, backup_location=state.backup_location())

    try:
        # Execute git with captured arguments
        result = subprocess.run(["git", "pull"], check=False, cwd=state.repo)
    except Exception as e:
        symlink_manager.patch()
        error(f"Failed to pull from git: {e}")
        return

    symlink_manager.patch()

    # Propagate git's exit code
    sys.exit(result.returncode)
    success("dotfiles are up to date.")
