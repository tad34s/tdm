import subprocess
from pathlib import Path

import click

import tdm.fs_utils as fs
from tdm.print_to_user import success, warning

sample_config = """
bootstrap = ""  

# files or directories to ignore when adding a whole repository
ignore = []

# files or directories that are in the files.toml but we do not want to symlink them
exclude = []

# list profile like so
# [profile-name]   
# bootstrap = ""  
# ignore = []
# exclude = []
"""


@click.command()
@click.argument("path")
@click.option("--git", "-g", is_flag=True, help="Prompt to add remote.")
def init(path: str, git: bool) -> None:
    """Initialize new dotfiles repository."""

    dirs = ["files", "forks", "bin"]
    dotfiles_repo = Path(path).resolve()
    if dotfiles_repo.exists():
        warning("Such directory already exists. It will be overwritten.", ask_continue=True)

    dotfiles_repo.mkdir(parents=True, exist_ok=True)

    if (dotfiles_repo / ".tdm").exists():
        fs.delete(dotfiles_repo / ".tdm")
    for directory in dirs:
        new_dir = dotfiles_repo / directory
        if new_dir.exists():
            fs.delete(new_dir)
        new_dir.mkdir(parents=True)

    with (dotfiles_repo / "config.toml").open("w") as f:
        f.write(sample_config)

    _ = subprocess.run(["git", "init"], check=False, cwd=dotfiles_repo, capture_output=True)

    if git:
        remote = input("Git remote: ")

        if remote:
            _ = subprocess.run(
                ["git", "remote", "add", "origin", remote],
                check=False,
                cwd=dotfiles_repo,
                capture_output=True,
            )
            _ = subprocess.run(
                ["git", "push", "-u", "origin", "master"],
                check=False,
                cwd=dotfiles_repo,
                capture_output=True,
            )

    success(f"initialized a tdm repo at \033[3m{dotfiles_repo.resolve()}\033[0m.")
