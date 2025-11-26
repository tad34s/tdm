from dataclasses import dataclass
from pathlib import Path

import tdm.fs_utils as fs


@dataclass
class SymlinkNode:
    relative_path: Path
    src_base: Path
    target_base: Path
    backup_base: Path | None = None

    def __post_init__(self):
        self.src_path = self.src_base / self.relative_path
        self.target_path = self.target_base / self.relative_path
        self.backup_path = self.backup_base / self.relative_path if self.backup_base else None

    def symlink(self):
        fs.ensure_parents(self.target_path)

        if self.target_path.exists():
            if self.target_path.is_symlink() and self.target_path.readlink() == self.src_path:
                return
            if self.backup_path:
                fs.ensure_parents(self.backup_path)
                fs.move_skip_present(self.target_path, self.backup_path)
            else:
                fs.delete(self.target_path)
        self.target_path.symlink_to(self.src_path)

    def desymlink(self, use_backup: bool):
        assert self.target_path.is_symlink(), (
            f"{self.target_path} - target is not a symlink when desymlinking"
        )
        self.target_path.unlink()
        if self.backup_path and use_backup and self.backup_path.exists():
            fs.move(self.backup_path, self.target_path)
            fs.clean_parents(self.backup_path)

    def desymlink_keep(self):
        assert self.target_path.is_symlink(), "target is not a symlink when desymlinking"
        self.target_path.unlink()
        fs.copy(self.src_path, self.target_path)

    def __eq__(self, value: object, /) -> bool:
        if type(value) is not type(self):
            return False
        return (
            self.src_path == value.src_path
            and self.target_path == value.target_path
            and self.backup_path == value.backup_path
        )
