import click

from tdm.commands import add, deploy, fork, git, init, patch, rejoin, rm, status, use, vacate


@click.group()
def cli() -> None:
    """Dotfiles Manager CLI"""


cli.add_command(add)
cli.add_command(deploy)
cli.add_command(rm)
cli.add_command(fork)
cli.add_command(init)
cli.add_command(rejoin)
cli.add_command(use)
cli.add_command(vacate)
cli.add_command(patch)
cli.add_command(git)
cli.add_command(status)
