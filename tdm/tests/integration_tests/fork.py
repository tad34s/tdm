from pathlib import Path

from click.testing import CliRunner

from tdm.cli import cli
from tdm.tests.fixtures import *
from tdm.tests.utils import assert_result

# NOTE: Fork
# Fork should work as follows:
# - Fork takes the current version of the file in the base profile and makes it a different file for the current profile
# - When the base profile is active you cannot fork
# - When forking:
#   - A child of a forked dir - does nothing (already forked) returns error
#   - A parent of a forked dir - warns that a the child is forked
#                              - forks the rest of the files
#                              - removes child from forked_dirs
# - If a --profile is passed, the fork will copy the file from profile specified instead, will ask if is ok to repalce the current fork if exists.
# - If the file specified is already forked it will do a warning and then simply replace the file
# - --symlink can be passes only when profile is specified. Instead of copying will create a symlink.
#   - Now the file is kept the same between the two profiles, but different from base.


def test_fork_file(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert_result(result, "use")

    result = runner.invoke(cli, ["fork", ".bashrc"])
    assert_result(result, "fork", tmp_home)

    (tmp_home / ".bashrc").write_text("echo Different text")
    assert (tmp_home / ".bashrc").read_text() == "echo Different text"

    result = runner.invoke(cli, ["use", "base"])
    assert_result(result, "use", tmp_home)

    assert (tmp_home / ".bashrc").read_text() == "echo hello from bashrc"

    result = runner.invoke(cli, ["use", "linux-dev", "-b"])
    assert_result(result, "use", tmp_home)

    assert (tmp_home / ".bashrc").read_text() == "echo Different text"


def test_fork_dir(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert result.exit_code == 0, f"Use failed: {result.output}"

    result = runner.invoke(cli, ["fork", ".config/nvim"])
    assert_result(result, "Fork", tmp_home)

    assert (tmp_home / ".config" / "nvim" / "lua").is_symlink()
    assert "linux-dev" in str((tmp_home / ".config" / "nvim" / "lua").readlink())

    (tmp_home / ".config/nvim/lua/user/remaps.lua").write_text("echo Different remaps")
    assert (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text() == "echo Different remaps"

    result = runner.invoke(cli, ["use", "base"])
    assert_result(result, "Use", tmp_home)

    assert (
        tmp_home / ".config/nvim/lua/user/remaps.lua"
    ).read_text() == 'My remaps: \n vim vim.g.mapleader = " "'

    result = runner.invoke(cli, ["use", "linux-dev", "-b"])
    assert result.exit_code == 0, f"Use failed: {result.output}"

    assert (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text() == "echo Different remaps"
    assert (tmp_home / ".config" / "nvim" / "lua").is_symlink()
    assert "linux-dev" in str((tmp_home / ".config" / "nvim" / "lua").readlink())


def test_fork_symlink(tmp_home: Path, used_repo: Path, runner: CliRunner):
    """Test fork with symlink option"""
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert_result(result, "use", tmp_home)

    # First fork normally
    result = runner.invoke(cli, ["fork", ".bashrc"])
    assert_result(result, "fork", tmp_home)

    result = runner.invoke(cli, ["use", "mac"])
    assert_result(result, "use", tmp_home)

    # Now fork with symlink to different profile
    result = runner.invoke(
        cli, ["fork", ".bashrc", "--profile=linux-dev", "--symlink"], input="y\n"
    )
    assert_result(result, "fork with symlink", tmp_home)

    # Verify symlink was created
    fork_path = used_repo / "forks" / "mac" / ".bashrc"
    assert fork_path.is_symlink()
    assert "linux-dev" in str(fork_path.readlink())


def test_fork_symlink_err(tmp_home: Path, used_repo: Path, runner: CliRunner):
    """Test fork with symlink option"""
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert_result(result, "use", tmp_home)

    # First fork normally
    result = runner.invoke(cli, ["fork", ".bashrc"])
    assert_result(result, "fork", tmp_home)

    print(file_tree(tmp_home))
    # Now fork with symlink to different profile
    result = runner.invoke(cli, ["fork", ".bashrc", "--profile=mac", "--symlink"], input="y\n")
    assert result.exit_code != 0
    assert "The profile specified did not fork the selected path." in result.output

    result = runner.invoke(cli, ["fork", ".bashrc", "--symlink"])
    assert result.exit_code != 0


def test_fork_non_existent_resource(tmp_home: Path, used_repo: Path, runner: CliRunner):
    """Test forking a non-existent resource"""
    result = runner.invoke(cli, ["fork", "/non/existent/file"])
    assert result.exit_code != 0
    assert "Resource does not exist" in result.output


def test_forking_base(tmp_home: Path, used_repo: Path, runner: CliRunner):
    """Forking when inside the base profile shoud fail."""
    result = runner.invoke(cli, ["use", "base"])
    result = runner.invoke(cli, ["fork", ".config/nvim"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_forking_child(tmp_home: Path, used_repo: Path, runner: CliRunner):
    """Forking a child of a forked directory."""
    result = runner.invoke(cli, ["use", "linux-dev"])
    result = runner.invoke(cli, ["fork", ".config/nvim/lua/"])
    assert_result(result, "fork")

    # should fail
    result = runner.invoke(cli, ["fork", ".config/nvim/lua/users"])
    assert result.exit_code != 0
    assert "Error" in result.output

    result = runner.invoke(cli, ["use", "base"])

    (tmp_home / ".config/nvim/lua/user/remaps.lua").write_text("echo Different remaps")

    result = runner.invoke(cli, ["fork", ".config/nvim/lua/users"])
    assert result.exit_code != 0
    assert "Error" in result.output

    result = runner.invoke(cli, ["use", "linux-dev"])
    # warning, will just replace the fork
    # passing the profile variable means we are changing the content of a fork
    result = runner.invoke(cli, ["fork", ".config/nvim", "--profile=base"], input="y\nn\n")
    print(result.output)
    assert result.exit_code != 0
    assert "Warning" in result.output

    # warning, will just replace the fork with a symlink to another fork
    result = runner.invoke(
        cli, ["fork", ".config/nvim", "--profile=base", "--symlink"], input="y\ny\n"
    )
    assert_result(result, "fork", tmp_home)
    assert "Warning" in result.output

    assert "echo Different remaps" in (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text()

    print("------")
    print(file_tree(tmp_home))
    result = runner.invoke(cli, ["fork", ".config/nvim/lua", "--profile=base", "-s"], input="y\n")
    assert result.exit_code != 0
    assert "Error" in result.output
    assert "Symlink" in result.output


def test_forking_parent(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])
    result = runner.invoke(cli, ["fork", ".config/nvim/lua/user"])
    assert_result(result, "fork")

    (tmp_home / ".config/nvim/lua/user/remaps.lua").write_text("some remaps")

    result = runner.invoke(cli, ["fork", ".config/nvim/lua"], input="n\n")
    assert result.exit_code != 0
    assert "Warning" in result.output

    result = runner.invoke(cli, ["fork", ".config/nvim/lua"], input="y\n")
    assert_result(result, "fork")

    assert "some remaps" in (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text()
    # Make sure the information about the child being forked is deleted
    assert (
        ".config/nvim/lua/user"
        not in (used_repo / "forks" / "linux-dev" / ".forked_dirs").read_text()
    )

    result = runner.invoke(cli, ["use", "base"])

    (tmp_home / ".config/nvim/lua/user/remaps.lua").write_text("echo Different remaps")

    result = runner.invoke(cli, ["fork", ".config/nvim/lua/users"])
    assert result.exit_code != 0
    assert "Error" in result.output

    result = runner.invoke(cli, ["use", "linux-dev"])

    # warning, will just replace the fork
    # passing the profile variable means we are changing the content of a fork
    result = runner.invoke(cli, ["fork", ".config/nvim", "--profile=base"], input="n\n")
    assert result.exit_code != 0
    assert "Warning" in result.output

    # warning, will just replace the fork with a symlink to another fork
    result = runner.invoke(cli, ["fork", ".config/nvim", "--profile=base"], input="y\ny\n")
    assert_result(result, "fork")
    assert "Warning" in result.output

    assert "echo Different remaps" in (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text()

    result = runner.invoke(
        cli, ["fork", ".config/nvim", "--profile=base", "--symlink"], input="y\ny\n"
    )
    assert_result(result, "fork")
    assert "Warning" in result.output
    assert (tmp_home / ".config/nvim/lua").is_symlink()


def test_fork_sibling_dirs(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])
    result = runner.invoke(cli, ["fork", ".config/nvim"])
    assert_result(result, "Fork", tmp_home)

    result = runner.invoke(cli, ["fork", ".config/polybar"])
    assert_result(result, "Fork", tmp_home)


def test_forking_already_forked(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])
    result = runner.invoke(cli, ["fork", ".config/nvim"])
    assert_result(result, "fork")

    (tmp_home / ".config/nvim/lua/user/remaps.lua").write_text("echo Different remaps")

    # Already forked
    result = runner.invoke(cli, ["fork", ".config/nvim"])
    assert result.exit_code != 0
    assert "Error" in result.output
    assert "echo Different remaps" in (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text()

    result = runner.invoke(cli, ["use", "linux-dev-notebook"])

    result = runner.invoke(cli, ["fork", ".config/nvim"])
    assert_result(result, "fork")

    assert (
        "echo Different remaps" not in (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text()
    )

    # Already forked
    result = runner.invoke(cli, ["fork", ".config/nvim"])
    assert result.exit_code != 0
    assert "Error" in result.output

    # The profile specified is the current profile
    result = runner.invoke(
        cli, ["fork", ".config/nvim", "--profile=linux-dev-notebook"], input="y\n"
    )
    assert result.exit_code != 0
    assert "Error" in result.output

    # Will ask if you want to overwrite
    result = runner.invoke(cli, ["fork", ".config/nvim", "--profile=linux-dev"], input="y\n")
    assert_result(result, "fork")
    assert "Warning" in result.output

    assert "echo Different remaps" in (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text()

    # Will ask if you want to overwrite
    result = runner.invoke(
        cli, ["fork", ".config/nvim", "--profile=linux-dev", "--symlink"], input="y\n"
    )
    assert_result(result, "fork")
    assert "Warning" in result.output
    assert "linux-dev" in str((tmp_home / ".config" / "nvim" / "lua").resolve())

    assert "echo Different remaps" in (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text()


def test_fork_parent_of_excluded_child(tmp_home: Path, used_repo: Path, runner: CliRunner):
    (tmp_home / ".config" / "polybar" / "picom.conf").touch()
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "patch")

    result = runner.invoke(cli, ["use", "mac"])
    assert_result(result, "use", tmp_home)

    assert not (tmp_home / ".config" / "polybar" / "picom.conf").exists()

    result = runner.invoke(cli, ["fork", ".config/polybar"])
    assert_result(result, "fork")

    assert not (tmp_home / ".config" / "polybar" / "picom.conf").exists()
