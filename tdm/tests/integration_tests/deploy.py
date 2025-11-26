import shutil
from pathlib import Path
from unittest.mock import Mock

from click.testing import CliRunner
from git import Repo

from tdm.cli import cli
from tdm.tests.fixtures import *
from tdm.tests.fixtures import FILES
from tdm.tests.utils import assert_result, check_files, check_symlinked


def test_deploy_command(deployed_repo: Path, tmp_home: Path) -> None:
    """Test deployment of a repo"""
    # Verify state files
    state_file = tmp_home / ".local" / "share" / "tdm" / "state"
    assert state_file.exists()


def test_deploy_command_forks(
    used_repo: Path,
    additional_dotfiles: Path,
    tmp_home: Path,
    runner: CliRunner,
) -> None:
    """Test deployment of a repo"""

    state_file = tmp_home / ".local" / "share" / "tdm" / "state"
    assert state_file.exists()

    result = runner.invoke(cli, ["deploy", "dotfiles"])
    assert_result(result, "Deploy")
    check_files(FILES, tmp_home)

    result = runner.invoke(cli, ["use", "linux-dev"])
    assert_result(result, "use")

    result = runner.invoke(cli, ["fork", ".config/polybar"])
    assert_result(result, "fork", tmp_home)
    check_files(FILES, tmp_home)

    symlinked: list[Path] = [
        tmp_home / x
        for x in [
            ".bashrc",
        ]
    ]
    check_symlinked(symlinked)

    result = runner.invoke(cli, ["deploy", "teckafiles"])
    assert_result(result, "Deploy")
    check_files(FILES, tmp_home)

    # check_symlinked(symlinked)

    result = runner.invoke(cli, ["vacate"])
    assert_result(result, "Vacate")

    result = runner.invoke(cli, ["deploy", "dotfiles"])
    assert_result(result, "Deploy")
    check_files(FILES, tmp_home)

    check_symlinked(symlinked)

    result = runner.invoke(cli, ["vacate"])
    assert_result(result, "Vacate")

    result = runner.invoke(cli, ["deploy", "teckafiles"])
    assert_result(result, "Deploy")
    check_files(FILES, tmp_home)


def test_deploy_invalid_directory(tmp_home, runner: CliRunner):
    """Test deploy with non-existent directory"""
    result = runner.invoke(cli, ["deploy", "/non/existent/path"])
    assert result.exit_code != 0
    assert "Directory provided does not exist" in result.output


def test_deploy_non_tdm_repo(tmp_home, runner: CliRunner):
    """Test deploy with directory that's not a TDM repo"""
    # Create a directory that's not a TDM repo
    non_repo = tmp_home / "not-a-repo"
    non_repo.mkdir()

    result = runner.invoke(cli, ["deploy", str(non_repo)])
    assert result.exit_code != 0
    assert "Not a valid tdm repo" in result.output


def test_command_without_deployment(tmp_home, runner: CliRunner):
    """Test commands fail when no TDM is deployed"""
    commands = [
        ["add", ".bashrc"],
        ["rm", ".bashrc"],
        ["fork", ".bashrc"],
        ["rejoin", ".bashrc"],
        ["use", "new-profile"],
        ["vacate"],
    ]

    for cmd in commands:
        result = runner.invoke(cli, cmd)
        assert result.exit_code != 0, f"{cmd} should fail without deployment"
        assert "No tdm repo deployed" in result.output


def test_bootstrap_on_deploy(tmp_home, tdm_prepped_repo, runner: CliRunner):
    """Test bootstrap script runs on deployment"""

    # Deploy with bootstrap
    result = runner.invoke(cli, ["deploy", str(tdm_prepped_repo), "--bootstrap", "-p", "linux-dev"])
    assert_result(result, "deploy with bootstrap", tmp_home)

    assert (tmp_home / "bootstrap_ran_linux").exists()


def test_deploy_from_github_repo_already_exists(
    monkeypatch, additional_dotfiles: Path, tmp_home: Path, runner: CliRunner
) -> None:
    """Test deployment from a GitHub repository URL"""

    result = runner.invoke(cli, ["vacate"])

    # Mock Repo.clone_from to copy our test repo instead of cloning
    def mock_clone_from(url: str, to_path: Path, depth=None):
        shutil.copytree(additional_dotfiles, to_path)
        return Mock(spec=Repo)

    monkeypatch.setattr(Repo, "clone_from", mock_clone_from)

    # Deploy using GitHub URL
    result = runner.invoke(cli, ["deploy", "https://github.com/testuser/teckafiles.git"])
    assert result.exit_code != 0, "Such folder already exists"
    assert "exists" in result.output


def test_deploy_from_github_repo(
    monkeypatch, additional_dotfiles: Path, tmp_home: Path, runner: CliRunner
) -> None:
    """Test deployment from a GitHub repository URL"""

    result = runner.invoke(cli, ["vacate"])

    # Mock Repo.clone_from to copy our test repo instead of cloning
    def mock_clone_from(url: str, to_path: Path, depth=None):
        shutil.copytree(additional_dotfiles, to_path)
        return Mock(spec=Repo)

    monkeypatch.setattr(Repo, "clone_from", mock_clone_from)

    # Deploy using GitHub URL
    result = runner.invoke(cli, ["deploy", "https://github.com/testuser/teckafiles2.git"])
    assert_result(result, "deploy", tmp_home)

    assert "teckafiles2" in (tmp_home / ".local" / "share" / "tdm" / "state").read_text()
