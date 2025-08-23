import shutil
import subprocess
from pathlib import Path
from shutil import rmtree

from tdm.config import Config
from tdm.fs_utils import add_to_set_file, delete, move, read_set_file, remove_from_set_file
from tdm.print_to_user import error
from tdm.symlink_utils import desymlink_dir, desymlink_fork, symlink_and_backup_item

APP_NAME = "tdm"


class State:
    BASE_PROFILE = "base"
    FORK_DIR_NAME = "forks"
    FILE_DIR_NAME = "files"
    FORK_BACKUP_DIR = "base_files"
    BACKUP_DIR = "original_files"
    ADDED_DIRS = "added_dirs"
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

    def fork_dir_p(self, profile: str) -> Path:
        return self.repo / self.FORK_DIR_NAME / profile

    @property
    def forked_dirs(self) -> set[str]:
        forked_dirs_file = self.repo / self.FORK_DIR_NAME / self.profile / self.FORKED_DIRS_FILE
        return read_set_file(forked_dirs_file)

    @property
    def added_dirs(self) -> set[str]:
        added_dirs_file = self.repo / self.REPO_DATA_DIR / self.ADDED_DIRS
        return read_set_file(added_dirs_file)

    @property
    def profile_fork_dirs(self):
        """Yields: Paths to directories where each profile stores their forks."""
        for fork_dir in (self.repo / self.FORK_DIR_NAME).iterdir():
            yield fork_dir

    def backup_location(self, create: bool = False) -> Path:
        path = self.get_app_data_dir() / self.BACKUP_DIR
        if create:
            path.mkdir(exist_ok=True, parents=True)
        return path

    def fork_backup_location(self, create: bool = False) -> Path:
        path = self.get_repo_data_dir() / self.FORK_BACKUP_DIR
        if create:
            path.mkdir(exist_ok=True, parents=True)
        return path

    def add_forked_dir(self, forked_dir: str) -> None:
        forked_dirs_file = self.repo / self.FORK_DIR_NAME / self.profile / self.FORKED_DIRS_FILE

        assert add_to_set_file(forked_dirs_file, forked_dir)

    def remove_forked_dir(self, forked_dir: str) -> None:
        forked_dirs_file = self.repo / self.FORK_DIR_NAME / self.profile / self.FORKED_DIRS_FILE
        assert remove_from_set_file(forked_dirs_file, forked_dir)

    def remove_children_in_forked_dir(self, forked_dir: str) -> None:
        """Goes through each profiles forks and removes any children of forked_dir from the
        forked_dirs file.
        """
        for profile_fork_dir in self.profile_fork_dirs:
            forked_dirs_file = profile_fork_dir / self.FORKED_DIRS_FILE
            for str_path in read_set_file(forked_dirs_file):
                if str_path.startswith(forked_dir):  # is a child
                    remove_from_set_file(forked_dirs_file, str_path)

    def delete_forks(self, relative_fork_path: Path) -> None:
        """Delete all versions of this dotfile/dir for each profile it is present in.
        Checks if the fork exists before deleting.
        """

        for profile_fork_dir in self.profile_fork_dirs:
            forked_item = profile_fork_dir / relative_fork_path
            if not forked_item.exists():
                continue
            delete(forked_item)

            # if str(relative_fork_path) in self.forked_dirs:
            #     self.remove_forked_dir(str(relative_fork_path))

    def add_added_dir(self, added_dir: str) -> None:
        added_dirs_file = self.get_repo_data_dir(create=True) / self.ADDED_DIRS
        assert add_to_set_file(added_dirs_file, added_dir)

    def remove_added_dir(self, added_dir: str) -> None:
        added_dirs_file = self.get_repo_data_dir(create=True) / self.ADDED_DIRS
        assert remove_from_set_file(added_dirs_file, added_dir)

    def remove_children_in_added_dir(self, added_dir: str) -> None:
        for str_path in self.added_dirs:
            if str_path.startswith(added_dir):  # is a child
                self.remove_added_dir(str_path)

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
        try:
            state = cls(Path(repo_dir), profile)
        except Exception:
            error("Failed reading tdm repository", exit=False)
            return None
        return state

    def is_ignored(self, relative_path: Path) -> bool:
        return any(x in str(relative_path) for x in self.config.ignore)

    def is_excluded(self, relative_path: Path) -> bool:
        return any(x in str(relative_path) for x in self.config.exclude)

    def get_relative_path(self, resource: Path) -> Path:
        if self.fork_backup_location() in resource.parents:
            relative_path = resource.relative_to(self.fork_backup_location())
        elif self.fork_dir in resource.parents:
            relative_path = resource.relative_to(self.fork_dir)
        elif self.file_dir in resource.parents:
            relative_path = resource.relative_to(self.file_dir)
        else:
            relative_path = resource.relative_to(Path.home())
        return relative_path

    def save(self) -> None:
        app_dir = self.get_app_data_dir(create=True)
        state_file = app_dir / self.STATE_FILE_NAME
        with state_file.open("w") as f:
            f.writelines([str(self.repo) + "\n", self.profile + "\n"])

    def delete(self) -> None:
        app_dir = self.get_app_data_dir(create=True)
        state_file = app_dir / self.STATE_FILE_NAME
        state_file.unlink()

    def clean_app_dir(self) -> None:
        app_dir = self.get_app_data_dir()
        state_file = app_dir / self.STATE_FILE_NAME
        backup_dir = app_dir / self.BACKUP_DIR
        if state_file.exists():
            delete(state_file)
        if backup_dir.exists():
            delete(backup_dir)

    def is_managed(self, relative_path: Path) -> bool:
        dotfile_path = self.file_dir / relative_path

        if not dotfile_path.exists():
            return False

        if dotfile_path.is_file():
            return True

        if dotfile_path.is_dir():
            if any(str(relative_path).startswith(x) for x in self.added_dirs):
                return True
            else:
                return False

        assert False, "Should be unreachable"

    def is_forked(self, relative_path: Path) -> bool:
        for profile_fork_dir in self.profile_fork_dirs:
            forked_dirs_file = profile_fork_dir / self.FORKED_DIRS_FILE
            forked_dirs = read_set_file(forked_dirs_file)
            if str(relative_path) in forked_dirs:
                return True

            for forked_dir in forked_dirs:
                if str(relative_path).startswith(forked_dir):
                    return True

        return False

    def is_forked_by_current_profile(self, relative_path: Path) -> bool:
        if str(relative_path) in self.forked_dirs:
            return True

        for forked_dir in self.forked_dirs:
            if str(relative_path).startswith(forked_dir):
                return True

        return False

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
            print("No bootstrap specified.")
            return

        bootstrap_script = self.repo / self.BINARY_DIR / self.config.bootstrap

        if not bootstrap_script.exists():
            error("Bootstrap script specified does not exists.")

        print(f"Running bootstrap \033[3m{bootstrap_script.name}\033[0m...")

        try:
            result = subprocess.run(
                str(bootstrap_script),
                cwd=str(self.repo / self.BINARY_DIR),
            )
            if result.returncode != 0:
                if std_out := result.stderr.decode():
                    error(f"Failed to execute bootstrap: {std_out}.")

                elif std_out := result.stdout.decode():
                    error(f"Failed to execute bootstrap: {std_out}.")

                else:
                    error("Failed to execute bootstrap.")
        except Exception as e:
            error(f"Failed to execute bootstrap: {e}.")

    def apply_forks(self) -> None:
        """Symlink each fork to source"""

        def recursively_symlink_forks(directory: Path, forked_dirs: set[str]) -> None:
            for item in directory.iterdir():
                if item.name == self.FORKED_DIRS_FILE:
                    continue
                if item.is_file(follow_symlinks=True) or (
                    item.is_dir() and str(item.relative_to(self.fork_dir)) in forked_dirs
                ):
                    symlink_and_backup_item(
                        item,
                        self.fork_dir,
                        self.file_dir,
                        self.get_repo_data_dir(create=True) / self.FORK_BACKUP_DIR,
                    )
                elif item.is_dir(follow_symlinks=True):
                    recursively_symlink_forks(item, forked_dirs)

        profile_forks = self.fork_dir
        if not profile_forks.exists():
            return

        recursively_symlink_forks(profile_forks, self.forked_dirs)

    def unapply_forks(self) -> None:
        """Desymlink each fork from source."""

        def recursively_desymlink_forks(src_dir: Path) -> None:
            for item in src_dir.iterdir():
                if item.is_symlink():
                    desymlink_fork(
                        item,
                        self.file_dir,
                        self.get_repo_data_dir(create=True) / self.FORK_BACKUP_DIR,
                    )
                elif item.is_dir(follow_symlinks=True):
                    recursively_desymlink_forks(item)

        recursively_desymlink_forks(self.file_dir)

    def symlink(self) -> None:
        """Symlink necessary dotfiles"""
        from tdm.file_tree import create_tree, symlink_and_backup_tree

        self.apply_forks()
        added_dirs = self.added_dirs
        root_file_node = create_tree(
            self,
            self.file_dir,
            added_dirs,
        )
        symlink_and_backup_tree(root_file_node, self)

    def desymlink(self, keep: bool = False) -> None:
        """Desymlink all links made by the current state"""

        print(keep)
        backup_location = self.file_dir if keep else self.backup_location()
        desymlink_dir(self.file_dir, self.file_dir, Path.home(), backup_location, copy=keep)

        self.unapply_forks()

    def remove_backup(self, relative_path: Path):
        backup = self.get_app_data_dir() / self.BACKUP_DIR / relative_path
        if backup.exists():
            delete(backup)

    def copy_dir_to_repo(self, real_dir: Path) -> None:
        for item in real_dir.iterdir():
            if any(x in str(item) for x in self.config.ignore):
                continue
            if item.is_dir():
                self.copy_dir_to_repo(item)
            else:
                relative_path = item.relative_to(Path.home())
                dest_dotfiles = self.file_dir / relative_path
                dest_dotfiles.parent.mkdir(exist_ok=True, parents=True)
                shutil.copy(item, dest_dotfiles)

    def kickout_ignored(self, curr_src_dir: Path):
        for item in curr_src_dir.iterdir():
            if self.is_ignored(item):
                relative_path = item.relative_to(self.file_dir)
                target_path = Path.home() / relative_path
                target_path.parent.mkdir(exist_ok=True, parents=True)
                if target_path.is_dir():
                    rmtree(target_path)
                move(item, target_path)
            if item.is_dir():
                self.kickout_ignored(item)
