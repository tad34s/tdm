import subprocess
from pathlib import Path

import click

from config import Config
from file_tree import create_tree, symlink

APP_NAME = "tdm"


class State:
    FORK_DIR_NAME = "forks"
    FILE_DIR_NAME = "files"
    BASE_BACKUP_DIR = "base_backup"
    BACKUP_DIR = "original_files"
    SYMLINKED_DIRS = "symlink_dirs"
    REPO_DATA_DIR = ".tdm"
    STATE_FILE_NAME = "state"
    BINARY_DIR = "bin"
    FORKED_DIRS_FILE = ".forked_dirs"

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
    def current(cls) -> "State | None":
        """Load the state currently used"""
        app_dir = Path(click.get_app_dir(APP_NAME))
        state_file = app_dir / cls.STATE_FILE_NAME
        if not state_file.exists():
            return None
        with state_file.open("r") as f:
            repo_dir = f.readline()
            profile = f.readline()

        return cls(Path(repo_dir), profile)

    def save(self) -> None:
        app_dir = Path(click.get_app_dir(APP_NAME))
        state_file = app_dir / self.STATE_FILE_NAME
        with state_file.open("w") as f:
            f.writelines([str(self.repo), self.profile])

    def get_repo_data_dir(self, create=False) -> Path:
        data_dir = self.repo / self.REPO_DATA_DIR
        if create:
            data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    @staticmethod
    def get_app_data_dir(create=False) -> Path:
        app_dir = Path(click.get_app_dir(APP_NAME))
        if create:
            app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir

    def run_bootstrap(self) -> None:
        """Run the provided bootstrap if available"""
        if self.config.bootstrap:
            subprocess.run(
                str(self.repo / self.BINARY_DIR / self.config.bootstrap),
                cwd=str(self.repo / self.BINARY_DIR),
            )

    @staticmethod
    def symlink_item(
        item: Path, original_base: Path, new_base: Path, backup_location: Path
    ) -> None:
        backup_location.mkdir(exist_ok=True, parents=True)
        relative_path = item.relative_to(original_base)
        target_path = new_base / relative_path
        if target_path.exists():
            if target_path.is_symlink():
                target_path.unlink()
            else:
                target_path.replace(backup_location / relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.symlink_to(item, target_is_directory=item.is_dir())

    @staticmethod
    def desymlink_item(symlink_location: Path, base_path: Path, backup_location: Path) -> None:
        relative_path = symlink_location.relative_to(base_path)
        target_path = backup_location / relative_path
        if target_path.exists():
            target_path.replace(symlink_location)
        else:
            relative_path.unlink()

    def __apply_forks(self) -> None:
        """Symlink each fork to source"""

        def recursively_symlink_forks(directory: Path, forked_dirs: list[Path]) -> None:
            for item in directory.iterdir():
                if item.name == self.FORKED_DIRS_FILE:
                    continue
                if item.is_file(follow_symlinks=True) or (
                    item.is_dir() and str(item.relative_to(self.fork_dir)) in forked_dirs
                ):
                    self.symlink_item(
                        item,
                        self.fork_dir,
                        self.file_dir,
                        self.get_repo_data_dir(create=True) / self.BASE_BACKUP_DIR,
                    )
                elif item.is_dir(follow_symlinks=True):
                    recursively_symlink_forks(item, forked_dirs)

        profile_forks = self.fork_dir
        if not profile_forks.exists():
            return

        forked_dirs_file = self.fork_dir / self.FORKED_DIRS_FILE
        with forked_dirs_file.open("r") as f:
            forked_dirs_set = set(f.readlines())
        forked_dirs = list(Path(x) for x in forked_dirs_set)

        recursively_symlink_forks(profile_forks, forked_dirs)

    def symlink(self) -> None:
        """Symlink necessary dotfiles"""

        self.__apply_forks()
        repo_data_dir = self.get_repo_data_dir()
        if not repo_data_dir.exists():
            symlink_dirs = set()
        else:
            symlink_dirs_file = repo_data_dir / self.SYMLINKED_DIRS
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

        def recursively_desymlink(
            curr_dir: Path, symlink_location_base: Path, backup_location: Path
        ) -> None:
            for item in curr_dir.iterdir():
                relative_path = item.relative_to(self.file_dir)
                if (symlink_location_base / relative_path).is_symlink():
                    self.desymlink_item(
                        item,
                        symlink_location_base,
                        backup_location,
                    )
                elif item.is_dir():
                    recursively_desymlink(item, symlink_location_base, backup_location)

        # unapply symlinks to home
        recursively_desymlink(
            self.file_dir, Path.home(), self.get_repo_data_dir() / self.BACKUP_DIR
        )

        # unapply symlink to dotfiles (forks)
        recursively_desymlink(
            self.fork_dir, self.file_dir, self.get_app_data_dir() / self.BASE_BACKUP_DIR
        )
