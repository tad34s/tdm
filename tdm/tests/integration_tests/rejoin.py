from pathlib import Path

from click.testing import CliRunner

from tdm.cli import cli
from tdm.tests.fixtures import *
from tdm.tests.utils import assert_result


def test_rejoin_file(tmp_home: Path, used_repo: Path, runner: CliRunner):
    # fork
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert result.exit_code == 0, f"Use failed: {result.output}"
    result = runner.invoke(cli, ["fork", ".bashrc"])
    assert result.exit_code == 0, f"Fork failed: {result.output}"
    (tmp_home / ".bashrc").write_text("echo Different text")
    assert (tmp_home / ".bashrc").read_text() == "echo Different text"
    result = runner.invoke(cli, ["use", "base"])
    assert result.exit_code == 0, f"Use failed: {result.output}"
    result = runner.invoke(cli, ["use", "linux-dev", "-b"])
    assert result.exit_code == 0, f"Use failed: {result.output}"
    assert (tmp_home / ".bashrc").read_text() == "echo Different text"

    assert (used_repo / "files" / ".bashrc").is_symlink()
    # rejoin
    result = runner.invoke(cli, ["rejoin", ".bashrc"])
    assert_result(result, "rejoin", tmp_home)

    assert not (used_repo / "files" / ".bashrc").is_symlink()
    # correct content
    assert (tmp_home / ".bashrc").read_text() == "echo hello from bashrc"

    result = runner.invoke(cli, ["use", "base"])
    assert result.exit_code == 0, f"Use failed: {result.output}"

    assert (tmp_home / ".bashrc").read_text() == "echo hello from bashrc"

    # can fork again
    result = runner.invoke(cli, ["use", "linux-dev", "-b"])
    assert result.exit_code == 0, f"Use failed: {result.output}"
    result = runner.invoke(cli, ["fork", ".bashrc"])
    assert result.exit_code == 0, f"Fork failed: {result.output}"
    (tmp_home / ".bashrc").write_text("echo Different text")
    assert (tmp_home / ".bashrc").read_text() == "echo Different text"
    result = runner.invoke(cli, ["use", "base"])
    assert result.exit_code == 0, f"Use failed: {result.output}"
    result = runner.invoke(cli, ["use", "linux-dev", "-b"])
    assert result.exit_code == 0, f"Use failed: {result.output}"
    assert (tmp_home / ".bashrc").read_text() == "echo Different text"


def test_rejoin_dir(tmp_home: Path, used_repo: Path, runner: CliRunner):
    # fork
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert result.exit_code == 0, f"Use failed: {result.output}"
    result = runner.invoke(cli, ["fork", ".config/nvim"])
    assert_result(result, "Fork", tmp_home)
    (tmp_home / ".config/nvim/lua/user/remaps.lua").write_text("echo Different remaps")
    result = runner.invoke(cli, ["use", "base"])
    assert_result(result, "Use", tmp_home)
    assert (
        tmp_home / ".config/nvim/lua/user/remaps.lua"
    ).read_text() == 'My remaps: \n vim vim.g.mapleader = " "'

    result = runner.invoke(cli, ["use", "linux-dev", "-b"])

    assert (used_repo / "files" / ".config/nvim").is_symlink()

    result = runner.invoke(cli, ["rejoin", ".config/nvim"])
    assert_result(result, "rejoin", tmp_home)

    assert not (used_repo / "files" / ".config/nvim").is_symlink()
    # correct content
    assert (
        tmp_home / ".config/nvim/lua/user/remaps.lua"
    ).read_text() == 'My remaps: \n vim vim.g.mapleader = " "'

    result = runner.invoke(cli, ["use", "linux-dev", "-b"])

    assert (
        tmp_home / ".config/nvim/lua/user/remaps.lua"
    ).read_text() == 'My remaps: \n vim vim.g.mapleader = " "'

    # can fork again
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert result.exit_code == 0, f"Use failed: {result.output}"
    result = runner.invoke(cli, ["fork", ".config/nvim"])
    assert result.exit_code == 0, f"Fork failed: {result.output}"
    (tmp_home / ".config/nvim/lua/user/remaps.lua").write_text("echo Different remaps")
    result = runner.invoke(cli, ["use", "base"])
    assert_result(result, "Use", tmp_home)
    assert (
        tmp_home / ".config/nvim/lua/user/remaps.lua"
    ).read_text() == 'My remaps: \n vim vim.g.mapleader = " "'


def test_fork_rejoin_parents(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert_result(result, "use")

    result = runner.invoke(cli, ["fork", ".config/nvim"])
    assert_result(result, "fork")

    result = runner.invoke(cli, ["fork", ".config"])
    assert_result(result, "fork")

    result = runner.invoke(cli, ["rejoin", ".config"])
    assert_result(result, "rejoin")

    result = runner.invoke(cli, ["use", "base"])
    assert_result(result, "use")

    result = runner.invoke(cli, ["use", "linux-dev"])
    assert_result(result, "use")

    assert not (used_repo / "files" / ".config").is_symlink()
    assert not (used_repo / "files" / ".config" / "nvim").is_symlink()


def test_rejoin_keep(tmp_home: Path, used_repo: Path, runner: CliRunner):
    """Test rejoin with keep option"""
    # Setup fork
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert_result(result, "use", tmp_home)

    result = runner.invoke(cli, ["fork", ".bashrc"])
    assert_result(result, "fork", tmp_home)

    (tmp_home / ".bashrc").write_text("echo Forked text")

    # Rejoin with keep
    result = runner.invoke(cli, ["rejoin", ".bashrc", "--keep"])
    assert_result(result, "rejoin with keep", tmp_home)

    # Verify original file was replaced with forked version
    original_path = used_repo / "files" / ".bashrc"
    assert original_path.read_text() == "echo Forked text"


def test_rejoin_non_forked_resource(tmp_home, used_repo, runner: CliRunner):
    """Test rejoining a resource that wasn't forked"""
    result = runner.invoke(cli, ["rejoin", ".bashrc"])
    assert result.exit_code != 0
    assert "Resource was not forked" in result.output
