from pathlib import Path

from click.testing import CliRunner

from tdm.cli import cli
from tdm.tests.fixtures import *
from tdm.tests.fixtures import FILES
from tdm.tests.utils import assert_result, check_files


def test_rm_keep(tmp_home: Path, used_repo, runner: CliRunner):
    file = tmp_home / ".bashrc"
    file.write_text("modified bash")

    # testing keep
    result = runner.invoke(cli, ["rm", "-k", ".bashrc"])
    assert_result(result, "rm", tmp_home)
    assert "modified bash" in file.read_text()

    result = runner.invoke(cli, ["add", ".bashrc"])
    assert_result(result, "add", tmp_home)

    # testing backup
    file.write_text("another bash")
    result = runner.invoke(cli, ["rm", "-b", ".bashrc"])
    assert_result(result, "rm", tmp_home)
    assert "modified bash" in file.read_text()


def test_rm_partially_symlinked(tmp_home, used_repo, runner: CliRunner):
    (tmp_home / ".config/polybar/.lazy-lock.json").touch()
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "patch", tmp_home)
    check_files(FILES, tmp_home)

    result = runner.invoke(cli, ["rm", "-b", ".config/polybar"])
    assert_result(result, "rm", tmp_home)
    assert not (tmp_home / ".config/polybar/config.ini").is_symlink()
    assert not (tmp_home / ".config/polybar/config.ini").is_symlink()
    check_files(FILES, tmp_home)

    result = runner.invoke(cli, ["add", ".config/polybar"])
    assert_result(result, "add", tmp_home)
    assert (tmp_home / ".config/polybar").is_symlink()
    check_files(FILES, tmp_home)


def test_remove_removes_changes(tmp_home, used_repo, runner: CliRunner):
    (tmp_home / ".config/polybar/hi").touch()
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "patch", tmp_home)
    result = runner.invoke(cli, ["rm", "-b", ".config/polybar"])
    assert_result(result, "rm", tmp_home)
    assert not (tmp_home / ".config/polybar/hi").exists()

    result = runner.invoke(cli, ["add", ".config/polybar"])
    assert_result(result, "add", tmp_home)

    assert not (tmp_home / ".config/polybar/hi").exists()


def test_rm_invalid_resource(tmp_home, used_repo, runner: CliRunner):
    """Test removing non-existent resource"""
    result = runner.invoke(cli, ["rm", "/non/existent/file"])
    assert result.exit_code != 0
    assert "Resource does not exist" in result.output


def test_rm_not_managed(tmp_home, used_repo, runner: CliRunner):
    """Test removing non-managed resource"""
    new_file = tmp_home / "hi"
    new_file.touch()
    result = runner.invoke(cli, ["rm", "hi"])
    assert result.exit_code != 0
    assert "not managed" in result.output
