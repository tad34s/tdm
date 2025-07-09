import shutil
import subprocess
from pathlib import Path

from tdm.config import Config
from tdm.print_to_user import error

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

    @property
    def forked_dirs(self) -> set[str]:
        forked_dirs_file = self.repo / self.FORK_DIR_NAME / self.profile / self.FORKED_DIRS_FILE
        if not forked_dirs_file.exists():
            return set()
        with forked_dirs_file.open("r") as f:
            forked_dirs = set(f.readlines())
        return forked_dirs

    @property
    def symlink_dirs(self) -> set[str]:
        symlink_dirs_file = self.repo / self.REPO_DATA_DIR / self.SYMLINKED_DIRS
        if not symlink_dirs_file.exists():
            return set()
        with symlink_dirs_file.open("r") as f:
            symlink_dirs = set(f.readlines())
        return symlink_dirs

    @staticmethod
    def add_to_set_file(file: Path, entry: str) -> bool:
        entries = []
        if file.exists():
            with file.open("r") as f:
                entries = set(f.readlines())
        if entry in entries:
            return False
        with file.open("a") as f:
            f.write(entry)
        return True

    @staticmethod
    def remove_from_set_file(file: Path, entry: str) -> bool:
        if not file.exists():
            return False
        with file.open("r") as f:
            entries = set(f.readlines())
        if entry not in entries:
            return False
        entries.remove(entry)
        if not entries:
            file.unlink()
        else:
            with file.open("w") as f:
                f.writelines(entries)
        return True

    def add_forked_dir(self, forked_dir: str) -> None:
        forked_dirs_file = self.repo / self.FORK_DIR_NAME / self.profile / self.FORKED_DIRS_FILE
        assert self.add_to_set_file(forked_dirs_file, forked_dir)

    def remove_forked_dir(self, forked_dir: str) -> None:
        forked_dirs_file = self.repo / self.FORK_DIR_NAME / self.profile / self.FORKED_DIRS_FILE
        assert self.remove_from_set_file(forked_dirs_file, forked_dir)

    def add_symlinked_dir(self, symlinked_dir: str) -> None:
        symlinked_dirs_file = self.get_repo_data_dir(create=True) / self.SYMLINKED_DIRS
        assert self.add_to_set_file(symlinked_dirs_file, symlinked_dir)

    def remove_symlinked_dir(self, symlinked_dir: str) -> None:
        symlinked_dirs_file = self.get_repo_data_dir(create=True) / self.SYMLINKED_DIRS
        assert self.remove_from_set_file(symlinked_dirs_file, symlinked_dir)

    @classmethod
    def current(cls) -> "State | None":
        """Load the state currently used"""
        app_dir = cls.get_app_data_dir()
        state_file = app_dir / cls.STATE_FILE_NAME
        if not state_file.exists():
            return None
        with state_file.open("r") as f:
            repo_dir = f.readline().strip()
            profile = f.readline().strip()

        return cls(Path(repo_dir), profile)

    def save(self) -> None:
        app_dir = self.get_app_data_dir(create=True)
        state_file = app_dir / self.STATE_FILE_NAME
        with state_file.open("w") as f:
            f.writelines([str(self.repo) + "\n", self.profile + "\n"])

    def get_repo_data_dir(self, create=False) -> Path:
        data_dir = self.repo / self.REPO_DATA_DIR
        if create:
            data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    @staticmethod
    def get_app_data_dir(create=False) -> Path:
        app_dir = Path("~/.local/share").expanduser() / APP_NAME
        if create:
            app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir

    def run_bootstrap(self) -> None:
        """Run the provided bootstrap if available"""

        if not self.config.bootstrap:
            return

        bootstrap_script = self.repo / self.BINARY_DIR / self.config.bootstrap

        if not bootstrap_script.exists():
            error("Bootstrap script specified does not exists.")

        subprocess.run(
            str(bootstrap_script),
            cwd=str(self.repo / self.BINARY_DIR),
        )

    @staticmethod
    def symlink_and_backup_item(
        item: Path, original_base: Path, new_base: Path, backup_location: Path
    ) -> None:
        relative_path = item.relative_to(original_base)
        target_path = new_base / relative_path
        if target_path.exists():
            if target_path.is_symlink():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
            else:
                backup_dest = backup_location / relative_path
                backup_dest.parent.mkdir(exist_ok=True, parents=True)
                target_path.replace(backup_dest)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.symlink_to(item, target_is_directory=item.is_dir())

    @staticmethod
    def symlink_item(item: Path, original_base: Path, new_base: Path) -> None:
        relative_path = item.relative_to(original_base)
        target_path = new_base / relative_path
        if target_path.exists():
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.symlink_to(item, target_is_directory=item.is_dir())

    @staticmethod
    def desymlink_item(item: Path, base_path: Path, backup_location: Path) -> None:
        relative_path = item.relative_to(base_path)
        target_path = backup_location / relative_path
        if target_path.exists():
            item.unlink()
            target_path.replace(item)
        else:
            item.unlink()

    def __apply_forks(self) -> None:
        """Symlink each fork to source"""

        def recursively_symlink_forks(directory: Path, forked_dirs: set[str]) -> None:
            for item in directory.iterdir():
                if item.name == self.FORKED_DIRS_FILE:
                    continue
                if item.is_file(follow_symlinks=True) or (
                    item.is_dir() and str(item.relative_to(self.fork_dir)) in forked_dirs
                ):
                    self.symlink_and_backup_item(
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

        recursively_symlink_forks(profile_forks, self.forked_dirs)

    def __unapply_forks(self) -> None:
        """Desymlink each fork from source."""

        def recursively_desymlink_forks(src_dir: Path) -> None:
            for item in src_dir.iterdir():
                if item.is_symlink():
                    self.desymlink_item(
                        item,
                        self.file_dir,
                        self.get_repo_data_dir(create=True) / self.BASE_BACKUP_DIR,
                    )
                elif item.is_dir(follow_symlinks=True):
                    recursively_desymlink_forks(item)

        recursively_desymlink_forks(self.file_dir)

    def symlink(self) -> None:
        """Symlink necessary dotfiles"""
        from tdm.file_tree import create_tree, symlink_and_backup

        self.__apply_forks()
        symlink_dirs = self.symlink_dirs
        root_file_node = create_tree(
            self,
            self.file_dir,
            symlink_dirs,
        )
        symlink_and_backup(root_file_node, self)

    def desymlink(self) -> None:
        """Desymlink all links made by the current state"""

        def recursively_desymlink(
            curr_dir: Path, symlink_location_base: Path, backup_location: Path
        ) -> None:
            for item in curr_dir.iterdir():
                relative_path = item.relative_to(self.file_dir)
                if (symlink_location_base / relative_path).is_symlink():
                    self.desymlink_item(
                        symlink_location_base / relative_path,
                        symlink_location_base,
                        backup_location,
                    )
                elif item.is_dir():
                    recursively_desymlink(item, symlink_location_base, backup_location)

        # unapply symlinks to home
        recursively_desymlink(
            self.file_dir,
            Path.home().expanduser(),
            self.get_app_data_dir(create=True) / self.BACKUP_DIR,
        )

        self.__unapply_forks()
