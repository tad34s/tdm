import click

from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_manager import SymlinkManager


@click.command()
@click.argument("profile_name")
@click.option("--bootstrap", "-b", is_flag=True, help="Run bootstrap script")
def use(profile_name: str, bootstrap: bool):
    """Switch to a different profile"""
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    symlink_manager = SymlinkManager.current(state, backup_location=state.backup_location())
    new_state = State(state.repo, profile_name)
    symlink_manager.state = new_state
    symlink_manager.patch()
    new_state.save()
    if bootstrap:
        new_state.run_bootstrap()

    success(f"now using the \033[3m{profile_name}\033[0m profile.")
