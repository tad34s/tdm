from pathlib import Path

import click

from tdm.print_to_user import error
from tdm.state import State


@click.command()
def status() -> None:
    state = State.current()
    if not state:
        error("No tdm repo deployed.")
        return
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    RESET = "\033[0m"

    print(f"Profile: {GREEN}{state.profile}{RESET}")
    print(f"Repo: {CYAN}{str(state.repo.relative_to(Path.home()))}{RESET}")
