import subprocess
import sys

import click

from tdm.print_to_user import error, success
from tdm.state import State


@click.command
def update():
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    state.desymlink()

    try:
        # Execute git with captured arguments
        result = subprocess.run(["git", "pull"], check=False, cwd=state.repo)
    except Exception as e:
        state.symlink()  # cleanup
        error(f"Failed to pull from git: {e}")
        return

    state.symlink()

    # Propagate git's exit code
    sys.exit(result.returncode)
    success("dotfiles are up to date.")
