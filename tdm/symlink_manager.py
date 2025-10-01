from pathlib import Path
from typing import Generator

import tdm.fs_utils as fs
from tdm.state import State
from tdm.symlink_node import SymlinkNode


class SymlinkManager:
    def __init__(
        self,
        state: State,
        src_dir: Path,
        target_dir: Path | None = None,
        backup_location: Path | None = None,
    ) -> None:
        self.src_dir = src_dir
        self.state = state
        self.target_dir = target_dir if target_dir else Path.home()
        self.backup_location = backup_location
        self.nodes = self.current_tree(self.state, self.target_dir, self.backup_location)

    @staticmethod
    def symlinked_nodes_iter(
        state: State, target_dir_base: Path, backup_location: Path | None
    ) -> Generator[SymlinkNode]:
        """Iterates over currently symlinked nodes."""
        for relative_path_str in state.symlinked_nodes:
            target_path = target_dir_base / relative_path_str
            if not target_path.is_symlink():
                continue
            relative_path = Path(relative_path_str)
            yield SymlinkNode(
                relative_path,
                fs.remove_relative(target_path.readlink(), relative_path),
                target_dir_base,
                backup_base=backup_location,
            )

    # TODO: if file not there maybe try to dicscover the tree - recover from bad state
    @staticmethod
    def current_tree(
        state: State, target_dir_base: Path, backup_location: Path | None
    ) -> list[SymlinkNode]:
        output = []
        iter = SymlinkManager.symlinked_nodes_iter(state, target_dir_base, backup_location)
        for node in iter:
            if not node.src_path.exists():  # the dotfile was somehow deleted, can happen
                print("unlinking", node.target_path)
                node.target_path.unlink()  # we delete the broken symlink
            else:
                output.append(node)
        return output

    def symlink(self):
        for node in self.nodes:
            node.symlink()
        self.state.update_symlinked_nodes(self.nodes)

    def desymlink(self, use_backup: bool = True):
        for node in self.nodes:
            node.desymlink(use_backup)
        self.state.update_symlinked_nodes([])

    def desymlink_keep(self):
        for node in self.nodes:
            node.desymlink_keep()

        self.state.update_symlinked_nodes([])

    def get_node(self, relative_path: Path) -> SymlinkNode | None:
        target_path = self.target_dir / relative_path
        if (
            not target_path.exists()
            or not target_path.is_symlink()
            or self.state.repo not in target_path.readlink().parents
        ):
            return None

        return SymlinkNode(
            relative_path,
            fs.remove_relative(target_path.readlink(), relative_path),
            self.target_dir,
            backup_base=self.backup_location,
        )

    def get_children(self, relative_path: Path) -> list[SymlinkNode]:
        children = []
        for node in self.nodes:
            if str(relative_path) in str(node.src_path):
                children.append(node)
        return children

    def forget_node(self, node: SymlinkNode):
        for i, saved_node in enumerate(self.nodes):
            if node == saved_node:
                self.nodes.pop(i)
                break
        self.state.update_symlinked_nodes(self.nodes)

    def remove_node_keep(self, node: SymlinkNode):
        if node.target_path.is_symlink():
            node.target_path.unlink()
        fs.move(node.src_path, node.target_path)
        self.forget_node(node)

    def remove_node_backup(self, node: SymlinkNode):
        if node.backup_path and node.backup_path.exists():
            if node.target_path.exists():
                fs.delete(node.target_path)
            fs.move(node.backup_path, node.target_path)
            fs.clean_parents(node.backup_path)

        self.forget_node(node)

    def remove_node_delete(self, node: SymlinkNode):
        node.target_path.unlink()
        self.forget_node(node)

    @staticmethod
    def __create_tree_rec(
        state: State,
        curr_src_dir: Path,
        target_dir_base: Path,
        src_dir_base: Path,
        backup_location: Path | None,
        added_dirs: set[str],
        dir_added: bool = False,
    ) -> tuple[list[SymlinkNode], bool]:
        if state.is_excluded(curr_src_dir) or state.is_ignored(curr_src_dir):
            return [], False
        relative_path = curr_src_dir.relative_to(src_dir_base)
        should_symlink_all = dir_added or str(relative_path) in added_dirs
        could_symlink_all = should_symlink_all

        children_to_symlink: list[SymlinkNode] = []

        for child in curr_src_dir.iterdir():
            child_relative = child.relative_to(src_dir_base)
            # excluding
            # ignored files should not appear in the repo, but they can (patch was not ran)
            if state.is_excluded(child_relative) or state.is_ignored(child_relative):
                could_symlink_all = False  # cannot symlink whole dir
                continue

            # We arrive first at the root of the fork because, we are going down the tree
            # meaning we do not care about children here
            # (if we stop the recursion after encountering a fork)
            # TODO: FIX, inside a fork dir can still be ignored stuff -> breaking at the fork node
            # we have to continue recursion
            if state.is_forked_by_current_profile(child_relative):
                if child.is_dir():
                    children_in_fork, could_symlink_child = SymlinkManager.__create_tree_rec(
                        state,
                        state.fork_dir / child_relative,
                        target_dir_base,
                        state.fork_dir,
                        backup_location,
                        added_dirs,
                        should_symlink_all,
                    )
                    children_to_symlink += children_in_fork

                    if not could_symlink_child:
                        could_symlink_all = False
                else:
                    children_to_symlink.append(
                        SymlinkNode(
                            relative_path=child_relative,
                            src_base=state.fork_dir,
                            target_base=target_dir_base,
                            backup_base=backup_location,
                        )
                    )

                # we are changing where to we symlink so we cannot symlink this whole node
                if src_dir_base == state.file_dir:
                    could_symlink_all = False  # cannot symlink whole dir
                continue

            if child.is_file(follow_symlinks=True):  # can always symlink a simple file
                children_to_symlink.append(
                    SymlinkNode(
                        relative_path=child_relative,
                        src_base=src_dir_base,
                        target_base=target_dir_base,
                        backup_base=backup_location,
                    )
                )

            elif child.is_dir(follow_symlinks=True):
                new_children, could_symlink_child = SymlinkManager.__create_tree_rec(
                    state,
                    child,
                    target_dir_base,
                    src_dir_base,
                    backup_location,
                    added_dirs,
                    should_symlink_all,
                )
                # check whether we could symlink whole child
                children_to_symlink += new_children
                if not could_symlink_child:
                    could_symlink_all = False

        # the corresponding dir in real home
        corresponding_dir = Path.home() / relative_path

        # check if we can really replace the whole corresponding dir
        # this is assuming that ignored files are not present in the repo
        if corresponding_dir.exists():
            for child in corresponding_dir.iterdir():
                if state.is_ignored(child):
                    could_symlink_all = False
                    break

        if could_symlink_all:
            return [
                SymlinkNode(
                    relative_path=relative_path,
                    src_base=src_dir_base,
                    target_base=target_dir_base,
                    backup_base=backup_location,
                )
            ], True

        return children_to_symlink, False

    @staticmethod
    def create_tree(
        state: State, src_dir: Path, target_dir: Path, backup_location: Path | None
    ) -> list[SymlinkNode]:
        nodes, _ = SymlinkManager.__create_tree_rec(
            state,
            src_dir,
            target_dir,
            state.file_dir,
            backup_location,
            state.added_dirs,
        )
        return nodes

    def kickout_ignored(self, node: SymlinkNode):
        curr_src_dir = node.src_path
        for item in curr_src_dir.iterdir():
            if self.state.is_ignored(item):
                relative_path = item.relative_to(node.src_base)
                target_path = Path.home() / relative_path
                target_path.parent.mkdir(exist_ok=True, parents=True)
                fs.move_skip_present(item, target_path)
                # fs.delete(item)

            if item.is_dir():
                item_node = SymlinkNode(
                    item.relative_to(node.src_base),
                    node.src_base,
                    node.target_base,
                    node.backup_base,
                )
                self.kickout_ignored(item_node)

    def patch(self):
        new_nodes = SymlinkManager.create_tree(
            self.state, self.src_dir, self.target_dir, self.backup_location
        )

        nodes_indices = set(range(len(self.nodes)))
        new_nodes_indices = set(range(len(new_nodes)))
        # found matches
        for i, node in enumerate(self.nodes):
            for j, new_node in enumerate(new_nodes):
                if new_node == node:
                    nodes_indices.remove(i)
                    new_nodes_indices.remove(j)
                    break

        # go over not matched
        for i in nodes_indices:
            node = self.nodes[i]
            node.desymlink(use_backup=True)
            if node.src_path.is_dir():
                self.kickout_ignored(node)

        for j in new_nodes_indices:
            new_node = new_nodes[j]
            new_node.symlink()

        self.nodes = new_nodes
        self.state.update_symlinked_nodes(self.nodes)
