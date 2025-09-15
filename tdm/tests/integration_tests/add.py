from pathlib import Path

from click.testing import CliRunner

from tdm.cli import cli
from tdm.fs_utils import move
from tdm.tests.fixtures import *
from tdm.tests.fixtures import FILES
from tdm.tests.utils import assert_result, check_files


def test_forcefully_removing_and_adding(tmp_home: Path, used_repo: Path, runner: CliRunner):
    file = used_repo / "files" / ".config/polybar"
    (tmp_home / ".config/polybar").unlink()
    move(file, tmp_home / ".config/polybar")

    result = runner.invoke(cli, ["patch"])

    result = runner.invoke(cli, ["add", ".config/polybar"])
    assert_result(result, "add", tmp_home)
    check_files(FILES, tmp_home)


def test_add_already_managed_file(tmp_home, used_repo, runner: CliRunner):
    """Test adding a file that's already managed"""
    result = runner.invoke(cli, ["add", ".bashrc"])
    print(result.output)
    assert result.exit_code != 0, "Should fail adding already managed file"
    assert "Already managing selected resource" in result.output


def test_add_already_managed_directory(tmp_home, used_repo, runner: CliRunner):
    """Test adding a directory that's already managed"""
    result = runner.invoke(cli, ["add", ".config/nvim"])
    assert result.exit_code != 0, "Should fail adding already managed directory"
    assert "Already managing selected resource" in result.output


def test_adding_child(tmp_home: Path, used_repo: Path, runner: CliRunner):
    """Test adding a child of managed dir"""
    result = runner.invoke(cli, ["add", ".config/nvim/lua"])
    assert result.exit_code != 0
    assert "Already managing selected resource" in result.output


def test_add_parent(tmp_home: Path, used_repo: Path, runner: CliRunner):
    (tmp_home / ".config" / "nvim" / ".lazy-lock.json").unlink()

    print(file_tree(tmp_home))
    result = runner.invoke(cli, ["add", ".config"], input="y\n")
    assert_result(result, "add", tmp_home)

    files = FILES.copy()
    files.remove(File(Path(".config/nvim/.lazy-lock.json"), "{}"))
    check_files(files, tmp_home)


def test_add_and_remove_parent(tmp_home: Path, used_repo: Path, runner: CliRunner):
    (tmp_home / ".config" / "nvim" / ".lazy-lock.json").unlink()

    new_contents = "new_contents\n"

    # this change should not change the backup
    (tmp_home / ".config" / "nvim" / "lua" / "user" / "opts.lua").write_text(new_contents)

    result = runner.invoke(cli, ["add", ".config"], input="y\n")
    assert_result(result, "add", tmp_home)

    files = FILES.copy()
    files.remove(File(Path(".config/nvim/.lazy-lock.json"), "{}"))

    # deleted the record of child being added
    assert "nvim" not in (tmp_home / "dotfiles" / ".tdm" / "added_dirs").read_text()

    result = runner.invoke(cli, ["rm", ".config"])
    assert_result(result, "rm", tmp_home)
    assert not (tmp_home / ".config").is_symlink()
    check_files(files, tmp_home)


def test_add_ignored(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["add", ".config/nvim/.lazy-lock.json"])
    print(result.output)
    assert result.exit_code != 0

    result = runner.invoke(cli, ["rm", ".config/nvim/"])

    result = runner.invoke(cli, ["add", ".config/nvim/.lazy-lock.json"])
    print(result.output)
    assert result.exit_code != 0


def test_add_excluded(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["use", "mac"])
    assert_result(result, "use", tmp_home)

    result = runner.invoke(cli, ["rm", ".config/picom.conf"])
    assert_result(result, "rm", tmp_home)
    assert not (used_repo / "files" / ".config/picom.conf").exists()

    result = runner.invoke(cli, ["add", ".config/picom.conf"], input="n\n")
    print(result.output)
    assert result.exit_code != 0

    result = runner.invoke(cli, ["add", ".config/picom.conf"], input="y\n")
    assert_result(result, "add")

    assert not (tmp_home / ".config/picom.conf").is_symlink()
    assert (used_repo / "files" / ".config/picom.conf").exists()


def test_add_excluded_parent_of_added(tmp_home: Path, used_repo: Path, runner: CliRunner):
    (tmp_home / ".config" / "new_dir").mkdir()
    (tmp_home / ".config" / "new_dir" / "picom.conf").touch()
    (tmp_home / ".config" / "new_dir" / "dotfile").touch()
    print(file_tree(tmp_home))
    result = runner.invoke(cli, ["use", "mac"])
    assert_result(result, "use")

    result = runner.invoke(cli, ["add", ".config/new_dir"])
    assert_result(result, "add", tmp_home)

    assert (used_repo / "files" / ".config" / "new_dir" / "picom.conf").exists()
    assert not (tmp_home / ".config" / "new_dir" / "picom.conf").is_symlink()
    assert (tmp_home / ".config" / "new_dir" / "dotfile").is_symlink()
    assert (tmp_home / ".config" / "new_dir" / "picom.conf").exists()


def test_add_and_remove_parent_with_forks(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])

    result = runner.invoke(cli, ["fork", ".config/polybar"])
    assert_result(result, "fork")

    result = runner.invoke(cli, ["add", ".config"], input="y\n")
    assert_result(result, "add", tmp_home)

    result = runner.invoke(cli, ["rm", ".config", "-k"])
    assert_result(result, "rm", tmp_home)

    assert (tmp_home / ".config").exists()


def test_add_invalid_resource(tmp_home, runner: CliRunner):
    """Test adding non-existent resource"""
    result = runner.invoke(cli, ["add", "/non/existent/file"])
    assert result.exit_code != 0
    assert "Resource does not exist" in result.output
