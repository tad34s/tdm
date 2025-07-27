import click

from tdm.print_to_user import error
from tdm.state import State


@click.command()
def push() -> None:
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return

    # git push
