import subprocess
from pathlib import Path

import click

from config import Config


class State:
    def __init__(self, repo: Path, profile: str) -> None:
        self.repo = repo
        self.profile = profile
        self.config = Config.load(repo, profile)

    @classmethod
    def current(cls) -> "State":
        """Load the state currently used"""
        app_dir = Path(click.get_app_dir("tdm"))
        state_file = app_dir / "state"
        with state_file.open("r") as f:
            repo_dir = f.readline()
            profile = f.readline()

        return cls(Path(repo_dir), profile)

    def run_bootstrap(self) -> None:
        """Run the provided bootstrap if available"""
        if self.config.bootstrap:
            subprocess.run(
                str(self.repo / "bin" / self.config.bootstrap),
                cwd=str(self.repo / "bin"),
            )

    def apply_forks(self) -> None:
        """Symlink each fork to source"""

    def symlink(self) -> None:
        """Symlink necessary dotfiles"""
        self.apply_forks()

    def desymlink(self) -> None:
        """Desymlink all links made by the current state"""
