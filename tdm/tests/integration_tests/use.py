from click.testing import CliRunner

from tdm.cli import cli
from tdm.tests.fixtures import *
from tdm.tests.utils import assert_result


def test_bootstrap_on_use(tmp_home, used_repo, runner: CliRunner):
    """Test bootstrap script runs when switching profiles"""
    profile = "linux-dev"

    # Switch profile with bootstrap
    result = runner.invoke(cli, ["use", profile, "--bootstrap"])
    assert_result(result, "use with bootstrap", tmp_home)

    # Verify bootstrap ran
    assert (tmp_home / "bootstrap_ran_linux").exists()


def test_use_invalid_profile(tmp_home, used_repo, runner: CliRunner):
    """Test switching to non-existent profile"""
    result = runner.invoke(cli, ["use", "non-existent-profile"])
    assert result.exit_code != 0
    assert "No such profile" in result.output or "Profile not found" in result.output
