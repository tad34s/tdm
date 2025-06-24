import subprocess
from pathlib import Path

import click

from config import Config
from file_tree import create_tree, symlink


class State:
    FORK_DIR_NAME = "forks"
    FILE_DIR_NAME = "files"
    BASE_BACKUP_DIR = "base_backup"
    BACKUP_DIR = "original_files"

    def __init__(self, repo: Path, profile: str) -> None:
        self.repo = repo
        self.profile = profile
        self.config = Config.load(repo, profile)

    @property
    def file_dir(self) -> Path:
        return self.repo / self.FILE_DIR_NAME

    @property
    def fork_dir(self) -> Path:
        return self.repo / self.FORK_DIR_NAME / self.profile

    @classmethod
    def current(cls) -> "State":
        """Load the state currently used"""
        app_dir = Path(click.get_app_dir("tdm"))
        state_file = app_dir / "state"
        with state_file.open("r") as f:
            repo_dir = f.readline()
            profile = f.readline()

        return cls(Path(repo_dir), profile)

    def get_repo_data_dir(self, create=False) -> Path:
        data_dir = self.repo / ".tdm/"
        if create:
            data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    @staticmethod
    def get_app_data_dir(create=False) -> Path:
        app_dir = Path(click.get_app_dir("tdm"))
        if create:
            app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir

    def run_bootstrap(self) -> None:
        """Run the provided bootstrap if available"""
        if self.config.bootstrap:
            subprocess.run(
                str(self.repo / "bin" / self.config.bootstrap),
                cwd=str(self.repo / "bin"),
            )

    @staticmethod
    def symlink_item(
        item: Path, original_base: Path, new_base: Path, backup_location: Path
    ) -> None:
        relative_path = item.relative_to(original_base)
        target_path = new_base / relative_path
        if target_path.exists():
            if target_path.is_symlink():
                target_path.unlink()
            if target_path.is_file():
                target_path.replace(backup_location / relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.symlink_to(item, target_is_directory=item.is_dir())

    def __apply_forks(self) -> None:
        """Symlink each fork to source"""

        def recursively_symlink_forks(directory: Path) -> None:
            forked_dirs = []
            forked_dirs_file = directory / "forked_dirs"
            if forked_dirs_file.exists():
                with forked_dirs_file.open("r") as f:
                    forked_dirs = f.readlines()

            for item in directory.iterdir():
                if item.name == "forked_dirs":
                    continue
                if item.is_file(follow_symlinks=True) or (
                    item.is_dir()
                    and str(item.relative_to(self.fork_dir)) in forked_dirs
                ):
                    self.symlink_item(
                        item,
                        self.fork_dir,
                        self.file_dir,
                        self.get_repo_data_dir(create=True) / self.BASE_BACKUP_DIR,
                    )
                elif item.is_dir(follow_symlinks=True):
                    recursively_symlink_forks(item)

        profile_forks = self.fork_dir
        if not profile_forks.exists():
            return

        recursively_symlink_forks(profile_forks)

    def symlink(self) -> None:
        """Symlink necessary dotfiles"""

        self.__apply_forks()
        repo_data_dir = self.get_repo_data_dir()
        if not repo_data_dir.exists():
            symlink_dirs = set()
        else:
            symlink_dirs_file = repo_data_dir / "symlink_dirs"
            with symlink_dirs_file.open("r") as f:
                symlink_dirs = set(f.readlines())

        root_file_node = create_tree(
            self,
            self.file_dir,
            symlink_dirs,
        )
        symlink(root_file_node, self)

    def desymlink(self) -> None:
        """Desymlink all links made by the current state"""
