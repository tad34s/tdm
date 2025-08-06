import click

from tdm.print_to_user import error, success
from tdm.state import State


@click.command()
@click.argument("profile_name")
@click.option("--bootstrap", "-b", is_flag=True, help="Run bootstrap script")
def use(profile_name: str, bootstrap: bool):
    """Switch to a different profile"""
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    state.desymlink()
    new_state = State(state.repo, profile_name)
    new_state.symlink()
    new_state.save()
    if bootstrap:
        new_state.run_bootstrap()

    success(f"now using the \033[3m{profile_name}\033[0m profile.")
