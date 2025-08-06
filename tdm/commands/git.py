import subprocess
import sys

import click

from tdm.print_to_user import error, print_git
from tdm.state import State


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,  # allow any Git flags/options
        help_option_names=[],  # disable click's help to pass '--help' to Git
    )
)
@click.argument("git_args", nargs=-1, type=click.UNPROCESSED)
def git(git_args) -> None:
    """Execute git commands in the current repository context"""

    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    state.unapply_forks()

    try:
        # Execute git with captured arguments
        result = subprocess.run(
            ["git", *git_args], check=False, cwd=state.repo, capture_output=True
        )
        print_git(result.stdout.decode())
        if result.stderr.decode():
            print_git(result.stderr.decode(), error=True)

    except Exception as e:
        state.apply_forks()  # cleanup
        error(f"Failed to execute git: {e}")
        return

    state.apply_forks()

    # Propagate git's exit code
    sys.exit(result.returncode)
