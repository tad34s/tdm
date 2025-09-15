from pathlib import Path

import click
from git import Repo

from tdm.print_to_user import error, success
from tdm.state import State
from tdm.symlink_manager import SymlinkManager


def is_git_url(arg: str) -> bool:
    return arg.endswith(".git")


def is_tdm_repo(repo_dir: Path) -> bool:
    dirs = [State.FILE_DIR_NAME, State.FORK_DIR_NAME, State.BINARY_DIR]
    return all((repo_dir / subdir).exists() for subdir in dirs)


@click.command()
@click.argument("path")
@click.option("--profile", "-p", default="base", help="Profile to activate")
@click.option("--name", "-n", default=None, help="Name of the cloned directory")
@click.option("--bootstrap", "-b", is_flag=True, help="Run bootstrap script")
def deploy(path: str, profile: str, name: str | None, bootstrap: bool) -> None:
    """Deploy a dotfiles profile"""

    dotfiles_repo: Path = Path()
    if is_git_url(path):
        path_to_dir = Path().cwd() / name if name is not None else Path().cwd()
        repo = Repo.clone_from(path, path_to_dir)
        dotfiles_repo = Path(str(repo.working_tree_dir))
    else:
        dotfiles_repo = Path(path).resolve()
        if not dotfiles_repo.exists():
            error("Directory provided does not exist.")

    if not is_tdm_repo(dotfiles_repo):
        error("Not a valid tdm repo.")

    # remove symlinks from current state
    curr_state = State.current()
    if curr_state:
        symlink_manager = SymlinkManager(
            curr_state, curr_state.file_dir, backup_location=curr_state.backup_location()
        )
        symlink_manager.desymlink(True)

    # symlink new state
    state = State(dotfiles_repo, profile)
    symlink_manager = SymlinkManager(state, state.file_dir)
    symlink_manager.symlink()
    if bootstrap:
        state.run_bootstrap()

    state.save()
    success(
        f"Deployed the repo \033[3m{str(dotfiles_repo)}\033[0m, \033[3mset profile as {profile}\033[0m."
    )
