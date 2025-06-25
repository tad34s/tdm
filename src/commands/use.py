import click

from print_to_user import error
from state import State


@click.command()
@click.argument("profile_name")
@click.option("--bootstrap", "-b", is_flag=True, help="Run bootstrap script")
def use(profile_name, bootstrap):
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
        state.run_bootstrap()
