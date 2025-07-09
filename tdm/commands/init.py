from pathlib import Path

import click

from tdm.print_to_user import error

sample_config = """
bootstrap = ""  # no script

# files or directories to ignore when adding a whole repository
ignore = [ 
    ".lazy-lock.json"
]

# files or directories that are in the files.toml but we do not want to symlink them
exclude = [".gitconfig"]

[linux-dev]   
bootstrap = "linux.sh"  # overriding
include = [".gitconfig"] # overriding exclusion

[linux-dev-notebook]   
bootstrap = "linux.sh"  # overriding
include = [".gitconfig"] # overriding exclusion

[mac]
bootstrap = "mac.sh"   # overriding
exclude = ["picom.ini"] # adding to exclusion

[server] 
use-only = [  # if specifies will only use files or directories provided here
    "nvim"
]
"""


@click.command()
@click.argument("name")
def init(name: str) -> None:
    """Initialize new dotfiles repository"""

    dirs = ["files", "forks", "bin"]
    dotfiles_repo = Path(name).resolve()
    if dotfiles_repo.exists():
        error("Such directory already exists")

    dotfiles_repo.mkdir(parents=True)

    for directory in dirs:
        new_dir = dotfiles_repo / directory
        new_dir.mkdir(parents=True)

    with (dotfiles_repo / "config.toml").open("w") as f:
        f.write(sample_config)
