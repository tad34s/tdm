import click

from commands.init import init


@click.group()
def cli() -> None:
    """Dotfiles Manager CLI"""


cli.add_command(init)

#
#
# @cli.command()
# @click.option("--keep", "-k", is_flag=True, help="Keep files after removing symlinks")
# def vacate(keep):
#     """Remove deployed symlinks"""
#     vacate_profile(keep)
#
#
# @cli.command()
# @click.argument("profile_name")
# @click.option("--bootstrap", "-b", is_flag=True, help="Run bootstrap script")
# def use(profile_name, bootstrap):
#     """Switch to a different profile"""
#     state = read_state()
#     if not state:
#         click.echo("❌ No active deployment")
#         return
#
#     # Vacate current profile (keep files)
#     vacate_profile(keep_files=True)
#
#     # Deploy new profile
#     deploy_profile(state["repo"], profile_name, bootstrap)


if __name__ == "__main__":
    cli()
