import click

from tdm.print_to_user import error
from tdm.state import State


@click.command()
@click.argument("path")
def pull() -> None:
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    state.unapply_forks()

    # git pull

    state.apply_forks()
