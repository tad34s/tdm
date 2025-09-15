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

    state.clean_ignored_from_repo(state.file_dir)

    try:
        # Execute git with captured arguments
        result = subprocess.run(
            ["git", *git_args], check=False, cwd=state.repo, capture_output=True
        )

        if std_out := result.stdout.decode():
            print_git(result.stdout.decode())
        if err_out := result.stderr.decode():
            print_git(err_out, error=True)

    except Exception as e:
        error(f"Failed to execute git: {e}")
        return

    # Propagate git's exit code
    sys.exit(result.returncode)
