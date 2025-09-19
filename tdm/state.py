import shutil
import subprocess
from pathlib import Path

import tdm.fs_utils as fs
from tdm.config import Config
from tdm.print_to_user import error
from tdm.symlink_node import SymlinkNode

APP_NAME = "tdm"


class State:
    BASE_PROFILE = "base"
    FORK_DIR_NAME = "forks"
    FILE_DIR_NAME = "files"
    BACKUP_DIR = "original_files"
    ADDED_DIRS = "added_dirs"
    SYMLINKED_NODES = "symlinked_nodes"
    REPO_DATA_DIR = ".tdm"
    STATE_FILE_NAME = "state"
    BINARY_DIR = "bin"
    FORKED_DIRS_FILE = ".forked_dirs"

    def __init__(self, repo: Path, profile: str) -> None:
        self.repo = repo
        self.profile = profile
        self.config = Config.load(repo, profile)

        self.file_dir = self.repo / self.FILE_DIR_NAME
        self.fork_dir = self.repo / self.FORK_DIR_NAME / self.profile

    def fork_dir_p(self, profile: str) -> Path:
        return self.repo / self.FORK_DIR_NAME / profile

    @property
    def forked_dirs(self) -> set[str]:
        forked_dirs_file = self.repo / self.FORK_DIR_NAME / self.profile / self.FORKED_DIRS_FILE
        return fs.read_set_file(forked_dirs_file)

    @property
    def added_dirs(self) -> set[str]:
        added_dirs_file = self.repo / self.REPO_DATA_DIR / self.ADDED_DIRS
        return fs.read_set_file(added_dirs_file)

    @property
    def symlinked_nodes(self) -> set[str]:
        # the relative paths of nodes that were symlinked
        symlinked_nodes_file = self.repo / self.REPO_DATA_DIR / self.SYMLINKED_NODES
        return fs.read_set_file(symlinked_nodes_file)

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

    def add_forked_dir(self, forked_dir: str) -> None:
        forked_dirs_file = self.repo / self.FORK_DIR_NAME / self.profile / self.FORKED_DIRS_FILE

        assert fs.add_to_set_file(forked_dirs_file, forked_dir)

    def remove_forked_dir(self, forked_dir: str) -> None:
        forked_dirs_file = self.repo / self.FORK_DIR_NAME / self.profile / self.FORKED_DIRS_FILE
        assert fs.remove_from_set_file(forked_dirs_file, forked_dir)

    def remove_children_in_forked_dir(self, forked_dir: str) -> None:
        """Goes through each profiles forks and removes any children of forked_dir from the
        forked_dirs file.
        """
        for profile_fork_dir in self.profile_fork_dirs:
            forked_dirs_file = profile_fork_dir / self.FORKED_DIRS_FILE
            for str_path in fs.read_set_file(forked_dirs_file):
                if str_path.startswith(forked_dir):  # is a child
                    fs.remove_from_set_file(forked_dirs_file, str_path)

    def delete_forks(self, relative_fork_path: Path) -> None:
        """Delete all versions of this dotfile/dir for each profile it is present in.
        Checks if the fork exists before deleting.
        """

        for profile_fork_dir in self.profile_fork_dirs:
            forked_item = profile_fork_dir / relative_fork_path
            if not forked_item.exists():
                continue
            fs.delete(forked_item)

            # if str(relative_fork_path) in self.forked_dirs:
            #     self.remove_forked_dir(str(relative_fork_path))

    def add_added_dir(self, added_dir: str) -> None:
        added_dirs_file = self.get_repo_data_dir(create=True) / self.ADDED_DIRS
        assert fs.add_to_set_file(added_dirs_file, added_dir)

    def remove_added_dir(self, added_dir: str) -> None:
        added_dirs_file = self.get_repo_data_dir(create=True) / self.ADDED_DIRS
        assert fs.remove_from_set_file(added_dirs_file, added_dir)

    def remove_children_in_added_dir(self, added_dir: str) -> None:
        for str_path in self.added_dirs:
            if str_path.startswith(added_dir):  # is a child
                self.remove_added_dir(str_path)

    def update_symlinked_nodes(
        self,
        new_symlinked_nodes: list[SymlinkNode],
        old_symlinked_nodes: set[str] | None = None,
    ) -> None:
        symlinked_nodes_file = self.repo / self.REPO_DATA_DIR / self.SYMLINKED_NODES
        if old_symlinked_nodes is None and symlinked_nodes_file.exists():
            old_symlinked_nodes = self.symlinked_nodes

        if not new_symlinked_nodes:
            if symlinked_nodes_file.exists():
                symlinked_nodes_file.unlink()
            return

        if not symlinked_nodes_file.exists():
            symlinked_nodes_file.touch()

        new_symlinked_nodes_set = set(str(x.relative_path) for x in new_symlinked_nodes)
        if old_symlinked_nodes and old_symlinked_nodes.issubset(new_symlinked_nodes_set):
            with symlinked_nodes_file.open("a") as f:
                for entry in new_symlinked_nodes_set - old_symlinked_nodes:
                    f.write(entry + "\n")
        else:
            with symlinked_nodes_file.open("w") as f:
                for entry in new_symlinked_nodes_set:
                    f.write(entry + "\n")

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
        if repo_dir is None:
            return None
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
        if self.fork_dir in resource.parents:
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
            fs.delete(state_file)
        if backup_dir.exists():
            fs.delete(backup_dir)

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
            forked_dirs = fs.read_set_file(forked_dirs_file)
            if str(relative_path) in forked_dirs:
                return True

            for forked_dir in forked_dirs:
                if str(relative_path).startswith(forked_dir):
                    return True

        return False

    def is_forked_by_current_profile(self, relative_path: Path) -> bool:
        fork_path = self.fork_dir / relative_path
        if fork_path.exists() and fork_path.is_file():
            return True

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

    def remove_backup(self, relative_path: Path):
        backup = self.get_app_data_dir() / self.BACKUP_DIR / relative_path
        if backup.exists():
            fs.delete(backup)

    def copy_dir_to_repo(self, real_dir: Path) -> None:
        for item in real_dir.iterdir():
            if any(x in str(item) for x in self.config.ignore):
                continue
            if item.is_symlink() and (self.file_dir in item.readlink().parents):
                continue
            if item.is_dir():
                self.copy_dir_to_repo(item)
            else:
                relative_path = item.relative_to(Path.home())
                dest_dotfiles = self.file_dir / relative_path
                dest_dotfiles.parent.mkdir(exist_ok=True, parents=True)
                shutil.copy(item, dest_dotfiles)

    def clean_ignored_from_repo(self, curr_src_dir: Path):
        for item in curr_src_dir.iterdir():
            if self.is_ignored(item):
                relative_path = item.relative_to(self.file_dir)
                target_path = Path.home() / relative_path
                target_path.parent.mkdir(exist_ok=True, parents=True)
                fs.move_skip_present(item, target_path)
            if item.is_dir():
                self.clean_ignored_from_repo(item)
