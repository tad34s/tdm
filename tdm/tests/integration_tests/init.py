import tomllib
from pathlib import Path

from tdm.tests.fixtures import *


def test_init_command(tdm_prepped_repo: Path) -> None:
    """Test repository initialization"""
    assert (tdm_prepped_repo / "files").is_dir()
    assert (tdm_prepped_repo / "forks").is_dir()
    assert (tdm_prepped_repo / "bin").is_dir()
    assert (tdm_prepped_repo / "config.toml").is_file()

    # Verify config content
    with (tdm_prepped_repo / "config.toml").open("rb") as f:
        config = tomllib.load(f)
    assert config["bootstrap"] == ""
    assert ".lazy-lock.json" in config["ignore"]


def test_init_command_replace(used_repo: Path, tmp_home: Path, runner: CliRunner) -> None:
    result = runner.invoke(cli, ["init", "dotfiles"], input="y\n")
    assert_result(result, "init")
    assert not (tmp_home / "dotfiles" / ".tdm").exists()
