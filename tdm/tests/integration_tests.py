import io
import tomllib
import traceback
from pathlib import Path
from types import TracebackType

import pytest
from click.testing import CliRunner

from tdm.cli import cli
from tdm.tests.utils import assert_result, check_files, file_tree

FILES: list[tuple[Path, str]] = [
    (Path(".config/nvim/lua/user/remaps.lua"), 'My remaps: \n vim vim.g.mapleader = " "'),
    (Path(".config/picom.conf"), "# My picom config"),
    (Path(".bashrc"), "echo hello from bashrc"),
    (Path(".config/nvim/.lazy-lock.json"), "{}"),
    (Path(".gitconfig"), "# git config"),
]


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def tmp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create temporary home directory and set environment"""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(home)
    for file, content in FILES:
        new_file = home / file
        new_file.parent.mkdir(exist_ok=True, parents=True)
        with new_file.open("w") as f:
            f.write(content)
    print("Starting home:")
    print(file_tree(home))
    return home


@pytest.fixture
def tdm_prepped_repo(tmp_home: Path, runner: CliRunner) -> Path:
    """Initialize a new TDM repository"""
    repo = tmp_home / "dotfiles"
    input_stream = io.StringIO("\n")  # Simulates pressing Enter
    result = runner.invoke(cli, ["init", "--git", str(repo)], input="\n")
    assert_result(result, "Init", tmp_home)

    # Create sample dotfiles in the repository
    files_dir = repo / "files"

    # Create sample config file
    bashrc = files_dir / ".bashrc"
    bashrc.write_text("# Sample bash config")

    # Create sample config directory
    config_dir = files_dir / ".config" / "myapp"
    config_dir.mkdir(parents=True)

    # Create config file inside director
    (config_dir / "settings.json").write_text('{"theme": "dark"}')

    # Create nested directory structure
    deep_dir = files_dir / ".deep" / "nested" / "configs"
    deep_dir.mkdir(parents=True)
    (deep_dir / "prefs.toml").write_text("[ui]\nfont_size = 12")

    # Create executable in bin directory
    bin_dir = repo / "bin"
    bootstrap = bin_dir / "bootstrap.sh"
    bootstrap.write_text("#!/bin/bash\necho 'Bootstrapping...'")
    bootstrap.chmod(0o755)  # Make executable

    bootstrap_script = repo / "bin" / "linux.sh"
    bootstrap_script.write_text("#!/bin/bash\ntouch ~/bootstrap_ran_linux")
    bootstrap_script.chmod(0o755)

    return repo


@pytest.fixture
def deployed_repo(tdm_prepped_repo: Path, runner: CliRunner, tmp_home: Path) -> Path:
    """Deploy a TDM repository"""
    result = runner.invoke(cli, ["deploy", str(tdm_prepped_repo), "--profile=base"])
    assert result.exit_code == 0, f"Deploy failed: {result.output}"

    return tdm_prepped_repo


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


def test_deploy_command(deployed_repo: Path, tmp_home: Path) -> None:
    """Test deployment of a repo"""
    # Verify state files
    state_file = tmp_home / ".local" / "share" / "tdm" / "state"
    assert state_file.exists()

    file_tree(tmp_home)


@pytest.fixture()
def used_repo(tmp_home: Path, runner: CliRunner):
    repo = tmp_home / "dotfiles"

    result = runner.invoke(cli, ["init", str(repo)])
    assert result.exit_code == 0, f"Init failed: {result.output}"

    result = runner.invoke(cli, ["deploy", str(repo)])
    assert result.exit_code == 0, f"Deploy failed: {result.output}"

    to_add = [
        tmp_home / ".config/nvim",
        tmp_home / ".config/picom.conf",
        tmp_home / ".bashrc",
    ]

    for file_to_add in to_add:
        result = runner.invoke(cli, ["add", str(file_to_add)])
        assert_result(result, "Add")

    print("\nAfter tdm use:")
    print(file_tree(tmp_home))

    assert (tmp_home / ".bashrc").is_symlink(), ".bashrc is not symlink"
    assert (tmp_home / ".config/picom.conf").is_symlink(), "picomf.conf is not symlink"
    assert not (tmp_home / ".config/nvim").is_symlink(), "nvim is a symlink"

    bootstrap_script = repo / "bin" / "linux.sh"
    bootstrap_script.write_text("#!/bin/bash\ntouch ~/bootstrap_ran_linux")
    bootstrap_script.chmod(0o755)

    check_files(FILES, tmp_home)

    return repo


def test_add_parent(tmp_home, used_repo, runner: CliRunner):
    (tmp_home / ".config" / "nvim" / ".lazy-lock.json").unlink()
    result = runner.invoke(cli, ["add", ".config"])
    assert_result(result, "add", tmp_home)

    files = FILES[0:3] + FILES[4:]
    check_files(files, tmp_home)


def test_add_and_remove_parent(tmp_home, used_repo, runner: CliRunner):
    (tmp_home / ".config" / "nvim" / ".lazy-lock.json").unlink()
    result = runner.invoke(cli, ["add", ".config"])
    assert_result(result, "add", tmp_home)

    files = FILES[0:3] + FILES[4:]

    print("symlinked dirs", (tmp_home / "dotfiles" / ".tdm" / "added_dirs").read_text())

    result = runner.invoke(cli, ["rm", ".config"])
    assert_result(result, "rm", tmp_home)
    check_files(files, tmp_home)


def test_use(used_repo, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert_result(result, "use")


def test_fork_file(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert result.exit_code == 0, f"Use failed: {result.output}"

    result = runner.invoke(cli, ["fork", ".bashrc"])
    assert result.exit_code == 0, f"Fork failed: {result.output}"

    (tmp_home / ".bashrc").write_text("echo Different text")
    assert (tmp_home / ".bashrc").read_text() == "echo Different text"

    result = runner.invoke(cli, ["use", "base"])
    assert result.exit_code == 0, f"Use failed: {result.output}"

    assert (tmp_home / ".bashrc").read_text() == "echo hello from bashrc"

    result = runner.invoke(cli, ["use", "linux-dev", "-b"])
    assert result.exit_code == 0, f"Use failed: {result.output}"

    assert (tmp_home / ".bashrc").read_text() == "echo Different text"


def test_fork_dir(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert result.exit_code == 0, f"Use failed: {result.output}"

    result = runner.invoke(cli, ["fork", ".config/nvim"])
    assert_result(result, "Fork")

    assert (used_repo / "files" / ".config/nvim").is_symlink()

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
    assert (used_repo / "files" / ".config/nvim").is_symlink()


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


def test_vacate(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert result.exit_code == 0, f"Use failed: {result.output}"

    (tmp_home / ".config/nvim/lua/user/remaps.lua").resolve().write_text("echo Different remaps")
    result = runner.invoke(cli, ["vacate"])
    assert_result(result, "vacate", tmp_home)
    print(file_tree(tmp_home))
    check_files(FILES, tmp_home)


def test_vacate_keep(tmp_home: Path, used_repo: Path, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert result.exit_code == 0, f"Use failed: {result.output}"
    (tmp_home / ".config/nvim/lua/user/remaps.lua").resolve().write_text("echo Different remaps")
    result = runner.invoke(cli, ["vacate", "-k"])
    files = [
        (Path(".config/nvim/lua/user/remaps.lua"), "echo Different remaps"),
        (Path(".config/picom.conf"), "# My picom config"),
        (Path(".bashrc"), "echo hello from bashrc"),
        (Path(".config/nvim/.lazy-lock.json"), "{}"),
        (Path(".gitconfig"), "# git config"),
    ]
    check_files(files, tmp_home)


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
    result = runner.invoke(cli, ["fork", ".bashrc", "--profile=linux-dev", "--symlink"])
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

    # Now fork with symlink to different profile
    result = runner.invoke(cli, ["fork", ".bashrc", "--profile=mac", "--symlink"])
    assert result.exit_code != 0
    assert "The profile specified did not fork the selected path." in result.output


# TODO: Change to test fork profile no symlink, verify contents
def test_fork_no_profile(tmp_home: Path, used_repo: Path, runner: CliRunner):
    """Test fork without specifying profile (uses current)"""
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert_result(result, "use", tmp_home)

    result = runner.invoke(cli, ["fork", ".bashrc"])
    assert_result(result, "fork", tmp_home)

    # Verify fork exists in current profile
    fork_path = used_repo / "forks" / "linux-dev" / ".bashrc"
    assert fork_path.exists()


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


def test_bootstrap_on_use(tmp_home, used_repo, runner: CliRunner):
    """Test bootstrap script runs when switching profiles"""
    profile = "linux-dev"

    # Switch profile with bootstrap
    result = runner.invoke(cli, ["use", profile, "--bootstrap"])
    assert_result(result, "use with bootstrap", tmp_home)

    # Verify bootstrap ran
    assert (tmp_home / "bootstrap_ran_linux").exists()


def test_fork_non_existent_resource(tmp_home, used_repo, runner: CliRunner):
    """Test forking a non-existent resource"""
    result = runner.invoke(cli, ["fork", "/non/existent/file"])
    assert result.exit_code != 0
    assert "Resource does not exist" in result.output


def test_rejoin_non_forked_resource(tmp_home, used_repo, runner: CliRunner):
    """Test rejoining a resource that wasn't forked"""
    result = runner.invoke(cli, ["rejoin", ".bashrc"])
    assert result.exit_code != 0
    assert "Resource was not forked" in result.output


def test_add_invalid_resource(tmp_home, runner: CliRunner):
    """Test adding non-existent resource"""
    result = runner.invoke(cli, ["add", "/non/existent/file"])
    assert result.exit_code != 0
    assert "Resource does not exist" in result.output


def test_rm_invalid_resource(tmp_home, used_repo, runner: CliRunner):
    """Test removing non-managed resource"""
    result = runner.invoke(cli, ["rm", "/non/existent/file"])
    assert result.exit_code != 0
    assert "Resource does not exist" in result.output


def test_use_invalid_profile(tmp_home, used_repo, runner: CliRunner):
    """Test switching to non-existent profile"""
    result = runner.invoke(cli, ["use", "non-existent-profile"])
    assert result.exit_code != 0
    assert "No such profile" in result.output or "Profile not found" in result.output


def test_patch(tmp_home: Path, used_repo: Path, runner: CliRunner):
    new_dir = tmp_home / ".config" / "nvim" / "plugins"
    new_dir.mkdir()
    (new_dir / "floaterminal.lua").touch()
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "Patch")
    print(file_tree(tmp_home))
    assert new_dir.is_symlink()


def test_patch_with_ignore(tmp_home: Path, used_repo: Path, runner: CliRunner):
    new_dir = tmp_home / ".config" / "nvim" / "plugins"
    new_dir.mkdir()
    (new_dir / "floaterminal.lua").touch()
    (new_dir / ".lazy-lock.json").touch()
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "Patch")
    print(file_tree(tmp_home))
    assert not (new_dir).is_symlink()
    assert (new_dir / "floaterminal.lua").is_symlink()


def test_patch_new_ignore(tmp_home: Path, used_repo: Path, runner: CliRunner):
    new_dir = tmp_home / ".config" / "nvim" / "plugins"
    new_dir.mkdir()
    (new_dir / "floaterminal.lua").touch()
    (new_dir / "lazy-lock.json").touch()
    result = runner.invoke(cli, ["patch"])
    # assert_result(result, "Patch")
    assert (new_dir).is_symlink()
    (new_dir / "lazy-lock.json").rename(new_dir / ".lazy-lock.json")
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "Patch")
    assert not (new_dir).is_symlink()
    assert (new_dir / "floaterminal.lua").is_symlink()


def test_patch_relinking(tmp_home: Path, used_repo: Path, runner: CliRunner):
    dir = tmp_home / ".config/nvim/lua"
    dir.unlink()
    assert not dir.exists()
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "Patch")
    check_files(FILES, tmp_home)


# ---- git ----


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
    backup_path = used_repo / ".tdm" / "base_backup" / ".bashrc"
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
