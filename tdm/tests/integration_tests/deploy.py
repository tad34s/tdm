from pathlib import Path

from click.testing import CliRunner

from tdm.cli import cli
from tdm.tests.fixtures import *
from tdm.tests.fixtures import FILES
from tdm.tests.utils import assert_result, check_files


def test_deploy_command(deployed_repo: Path, tmp_home: Path) -> None:
    """Test deployment of a repo"""
    # Verify state files
    state_file = tmp_home / ".local" / "share" / "tdm" / "state"
    assert state_file.exists()

    file_tree(tmp_home)


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
    assert_result(result, "fork")
    check_files(FILES, tmp_home)

    result = runner.invoke(cli, ["deploy", "teckafiles"])
    assert_result(result, "Deploy")
    check_files(FILES, tmp_home)

    result = runner.invoke(cli, ["vacate"])
    assert_result(result, "Vacate")

    result = runner.invoke(cli, ["deploy", "dotfiles"])
    assert_result(result, "Deploy")
    check_files(FILES, tmp_home)

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
