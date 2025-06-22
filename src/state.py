from pathlib import Path

from config import Config


class State:
    def __init__(self, repo: Path, profile: str, config: Config) -> None:
        self.repo = repo
        self.profile = profile
        self.config = config

    @staticmethod
    def current() -> "State":
        """Load the state currently used"""

    @staticmethod
    def load(repo: Path, profile: str) -> "State":
        """Load the state from a tdm repository"""

    def desymlink(self):
        """Desymlink all links made by the current state"""

    def symlink(self):
        """Symlink necessary dotfiles"""

    def run_bootstrap(self):
        """Run the provided bootstrap if available"""
