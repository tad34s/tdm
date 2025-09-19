import subprocess
from pathlib import Path

import click

from tdm.print_to_user import error
from tdm.state import State


@click.command
@click.argument("path")
@click.option(
    "--profile", "-p", default=None, help="Fetch the new contents from the profile selected."
)
def merge(path: str, profile: str | None):
    resource = Path(path).resolve()
    if not resource.exists():
        error("Resource does not exist.")

    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    if profile is None:
        profile = state.BASE_PROFILE

    if profile == state.profile:
        error("The profile specified is the current active profile.")

    remote_fork_dir = state.fork_dir_profile(profile)
    relative_path = state.get_relative_path(resource)

    try:
        # Run nvim directly in the terminal
        subprocess.run(
            ["nvim", "-d", str(resource), str(remote_fork_dir / relative_path)],
            check=False,
        )
    except FileNotFoundError:
        error("nvim is not installed or not found in PATH.")
    except Exception as e:
        error(f"Failed to execute merge tool: {e}")
