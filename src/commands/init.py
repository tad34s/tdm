from pathlib import Path

import click

from print_to_user import error

sample_config = """
bootstrap = ""    # global var

exclude-files = [                 # global exclude
 ".picom.tdmt"
]

ignore-files = [ # ignore when recursively adding
".lazy-lock.json"
]

[[profile]]                       # profile
name = "linux-dev"
bootstrap = "linux.sh"             # overriding

[[profile]]                       # profile
name = "mac"
include-files = [                        # special, includuje
 ".picom.tdmt"
]

[[profile]]                       # profile
name = "server"
use-only = [                            # pouzivej jenom tyhle
 "nvim"
]
"""


@click.command()
@click.argument("name")
def init(name: str) -> None:
    """Initialize new dotfiles repository"""

    dirs = ["files", "forks", "bin"]
    dotfiles_repo = Path(name)
    if dotfiles_repo.exists():
        error("Such directory already exists")

    dotfiles_repo.mkdir(parents=True)

    for directory in dirs:
        new_dir = dotfiles_repo / directory
        new_dir.mkdir(parents=True)

    with (dotfiles_repo / "config.toml").open("w") as f:
        f.write(sample_config)
