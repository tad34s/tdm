import traceback
from pathlib import Path
from types import TracebackType

from click.testing import CliRunner

from tdm.cli import cli
from tdm.tests.fixtures import *
from tdm.tests.utils import assert_result, file_tree


def test_git_without_deployment(runner: CliRunner):
    """Test git command without deployed TDM repo"""
    result = runner.invoke(cli, ["git", "status"])
    tracebakc_ig: TracebackType = result.exc_info[2]
    print(traceback.print_tb(tracebakc_ig))
    assert result.exit_code != 0
    assert "No tdm repo deployed" in result.output


# def test_git_command_in_repo(used_repo: Path, runner: CliRunner):
#     """Test git command executes in correct repository"""
#     result = runner.invoke(cli, ["git", "rev-parse", "--show-toplevel"])
#     assert_result(result, "git")
#     used_repo_str = str(used_repo)
#     assert result.exit_code == 0
#     assert used_repo_str in result.output


def test_git_command_restores_state(used_repo: Path, runner: CliRunner, tmp_home: Path):
    """Test git command restores fork state after execution"""
    # Create and fork a file
    runner.invoke(cli, ["use", "linux-dev"])
    runner.invoke(cli, ["fork", ".bashrc"])

    # Verify initial symlink state
    file_path = used_repo / "files" / ".bashrc"
    assert file_path.is_symlink()

    # Run git command
    result = runner.invoke(cli, ["git", "status"])
    assert result.exit_code == 0

    # Verify symlink was restored
    print(file_tree(tmp_home))
    assert file_path.is_symlink()


def test_git_sees_base_files(used_repo: Path, runner: CliRunner, tmp_home: Path):
    """Test git command sees base files (not forks) during execution"""
    # Create base file and commit it
    bashrc = used_repo / "files" / ".bashrc"
    bashrc.write_text("base")
    runner.invoke(cli, ["git", "add", "."], cwd=deployed_repo)
    runner.invoke(cli, ["git", "commit", "-m", "base file"], cwd=deployed_repo)

    # Fork and modify the file
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert_result(result, "use")
    result = runner.invoke(cli, ["fork", ".bashrc"])
    assert_result(result, "fork")
    fork_path = used_repo / "forks" / "linux-dev" / ".bashrc"
    fork_path.write_text("forked")

    # Modify backup (base) version
    backup_path = used_repo / ".tdm" / "base_files" / ".bashrc"
    backup_path.write_text("modified base")

    # Check git sees the modified base version
    result = runner.invoke(cli, ["git", "status", "-s", "files/.bashrc"])
    assert ".bashrc" in result.output


def test_git_command_failure_propagates(used_repo: Path, runner: CliRunner):
    """Test git command failure propagates exit code"""
    # Invalid git command
    result = runner.invoke(cli, ["git", "invalid-command"])
    assert result.exit_code != 0
    assert "invalid-command" in result.stderr


def test_git_command_with_flags(used_repo: Path, runner: CliRunner):
    """Test git command handles flags and arguments"""
    # Create test file
    test_file = used_repo / "files" / "test.txt"
    test_file.write_text("test")

    result = runner.invoke(cli, ["git", "add", "--verbose", "files/test.txt"])
    assert result.exit_code == 0
    assert "add 'files/test.txt'" in result.output
