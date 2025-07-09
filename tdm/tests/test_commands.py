import tomllib
import traceback
from pathlib import Path
from types import TracebackType

import pytest
from click.testing import CliRunner, Result

from tdm.cli import cli

FILES: list[tuple[Path, str]] = [
    (Path(".config/nvim/lua/user/remaps.lua"), 'My remaps: \n vim vim.g.mapleader = " "'),
    (Path(".config/picom.conf"), "# My picom config"),
    (Path(".bashrc"), "echo hello from bashrc"),
    (Path(".config/nvim/.lazy-lock.json"), "{}"),
    (Path(".gitconfig"), "# git config"),
]


def assert_result(result: Result, command_name: str):
    print(f"StdOut:\n{result.stdout}\nStdErr:{result.stderr}")
    print(f"Exception:{result.exception}")
    tracebakc_ig: TracebackType = result.exc_info[2]
    print(traceback.print_tb(tracebakc_ig))
    assert result.exit_code == 0, f"{command_name} failed\n"


def file_tree(path: Path, prefix: str = "", old_indent="", indent="   ") -> str:
    """Generate a string representation of the directory tree"""
    output = []
    is_root = old_indent == ""
    item_name = path.name
    if path.is_symlink():
        item_name = "\033[36m" + item_name + f" -> {path.readlink()}" + "\033[0m"
    elif path.is_dir():
        item_name = "\033[34m" + item_name + "/" + "\033[0m"

    item_text = f"{old_indent}{prefix}{item_name}"
    output.append(item_text)

    if path.is_dir():
        children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        count = len(children)
        for i, child in enumerate(children):
            is_last = i == count - 1
            if is_last:
                new_prefix = "└── "
                new_indent = indent + "   "
            else:
                new_prefix = "├── "
                new_indent = indent + "|  "

            child_output = file_tree(child, new_prefix, indent, new_indent)
            output.append(child_output)

    return "\n".join(output)


def check_files(files: list[tuple[Path, str]], home: Path):
    for file, content in files:
        real_file = home / file
        assert real_file.read_text() == content


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
    result = runner.invoke(cli, ["init", str(repo)])
    assert_result(result, "Init")

    # Create sample dotfiles in the repository
    files_dir = repo / "files"

    # Create sample config file
    bashrc = files_dir / ".bashrc"
    bashrc.write_text("# Sample bash config")

    # Create sample config directory
    config_dir = files_dir / ".config" / "myapp"
    config_dir.mkdir(parents=True)

    # Create config file inside directory
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
        assert result.exit_code == 0, f"Add failed: {result.output}"

    print("\nAfter tdm use:")
    print(file_tree(tmp_home))

    assert (tmp_home / ".bashrc").is_symlink(), ".bashrc is not symlink"
    assert (tmp_home / ".config/picom.conf").is_symlink(), "picomf.conf is not symlink"
    assert not (tmp_home / ".config/nvim").is_symlink(), "nvim is a symlink"

    check_files(FILES, tmp_home)

    return repo


def test_use(used_repo, runner: CliRunner):
    result = runner.invoke(cli, ["use", "linux-dev"])
    assert result.exit_code == 0, f"Use failed: {result.output}"


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
    assert result.exit_code == 0, f"Fork failed: {result.output}"

    (tmp_home / ".config/nvim/lua/user/remaps.lua").write_text("echo Different remaps")
    assert (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text() == "echo Different remaps"

    print(file_tree(tmp_home))
    result = runner.invoke(cli, ["use", "base"])
    assert_result(result, "Use")

    assert (
        tmp_home / ".config/nvim/lua/user/remaps.lua"
    ).read_text() == 'My remaps: \n vim vim.g.mapleader = " "'

    result = runner.invoke(cli, ["use", "linux-dev", "-b"])
    assert result.exit_code == 0, f"Use failed: {result.output}"

    assert (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text() == "echo Different remaps"


#
#
# def test_add_file(deployed_repo: Path, runner: CliRunner, tmp_home: Path) -> None:
#     """Test adding a file to management"""
#     # Create test file
#     test_file = tmp_home / ".testrc"
#     test_file.write_text("config")
#
#     result = runner.invoke(cli, ["add", str(test_file)])
#     assert result.exit_code == 0
#
#     # Verify file was added
#     repo_file = deployed_repo / "files" / ".testrc"
#     assert repo_file.is_file()
#     assert repo_file.read_text() == "config"
#
#     # Verify symlink created
#     assert (tmp_home / ".testrc").is_symlink()
#     assert os.readlink(tmp_home / ".testrc") == str(repo_file)
#
#
# def test_add_directory(deployed_repo: Path, runner: CliRunner, tmp_home: Path) -> None:
#     """Test adding a directory to management"""
#     # Create test directory
#     test_dir = tmp_home / ".config" / "app"
#     test_dir.mkdir(parents=True)
#     (test_dir / "config.toml").write_text("settings")
#
#     result = runner.invoke(cli, ["add", str(test_dir)])
#     assert result.exit_code == 0
#
#     # Verify directory was added
#     repo_dir = deployed_repo / "files" / ".config" / "app"
#     assert repo_dir.is_dir()
#     assert (repo_dir / "config.toml").is_file()
#
#     # Verify symlink created
#     assert (tmp_home / ".config" / "app").is_symlink()
#     assert os.readlink(tmp_home / ".config" / "app") == str(repo_dir)
#
#
# def test_fork_file(deployed_repo: Path, runner: CliRunner, tmp_home: Path) -> None:
#     """Test forking a managed file"""
#     # Setup: Add a file to manage
#     test_file = tmp_home / ".forkrc"
#     test_file.write_text("original")
#     runner.invoke(cli, ["add", str(test_file)])
#
#     # Fork the file
#     result = runner.invoke(cli, ["fork", str(test_file), "--profile=dev"])
#     assert result.exit_code == 0
#
#     # Verify fork exists
#     fork_file = deployed_repo / "forks" / "dev" / ".forkrc"
#     assert fork_file.exists()
#
#     # Modify the fork
#     fork_file.write_text("modified")
#
#     # Verify symlink points to fork
#     assert (tmp_home / ".forkrc").is_symlink()
#     assert os.readlink(tmp_home / ".forkrc") == str(fork_file)
#     assert (tmp_home / ".forkrc").read_text() == "modified"
#
#
# def test_switch_profile(deployed_repo: Path, runner: CliRunner, tmp_home: Path) -> None:
#     """Test switching between profiles"""
#     # Create fork in dev profile
#     test_file = tmp_home / ".switcher"
#     test_file.write_text("base")
#     runner.invoke(cli, ["add", str(test_file)])
#     runner.invoke(cli, ["fork", str(test_file), "--profile=dev"])
#
#     # Switch to dev profile
#     result = runner.invoke(cli, ["use", "dev"])
#     assert result.exit_code == 0
#
#     # Verify state updated
#     state_file = Path(click.get_app_dir("tdm")) / "state"
#     with state_file.open() as f:
#         content = f.read()
#         assert "dev" in content
#
#     # Verify fork is active
#     fork_file = deployed_repo / "forks" / "dev" / ".switcher"
#     assert (tmp_home / ".switcher").resolve() == fork_file
#
#
# def test_rejoin_file(deployed_repo: Path, runner: CliRunner, tmp_home: Path) -> None:
#     """Test rejoining a forked file to base"""
#     # Setup forked file
#     test_file = tmp_home / ".rejoinrc"
#     test_file.write_text("original")
#     runner.invoke(cli, ["add", str(test_file)])
#     runner.invoke(cli, ["fork", str(test_file), "--profile=dev"])
#
#     # Verify fork exists
#     fork_file = deployed_repo / "forks" / "dev" / ".rejoinrc"
#     assert fork_file.exists()
#
#     # Rejoin to base
#     result = runner.invoke(cli, ["rejoin", str(test_file)])
#     assert result.exit_code == 0
#
#     # Verify fork removed
#     assert not fork_file.exists()
#
#     # Verify symlink points to original
#     base_file = deployed_repo / "files" / ".rejoinrc"
#     assert (tmp_home / ".rejoinrc").resolve() == base_file
#
#
# def test_remove_file(deployed_repo: Path, runner: CliRunner, tmp_home: Path) -> None:
#     """Test removing a managed file"""
#     # Setup managed file
#     test_file = tmp_home / ".toremove"
#     test_file.write_text("data")
#     runner.invoke(cli, ["add", str(test_file)])
#
#     # Verify file is managed
#     assert (deployed_repo / "files" / ".toremove").exists()
#
#     # Remove file
#     result = runner.invoke(cli, ["rm", str(test_file)])
#     assert result.exit_code == 0
#
#     # Verify removal
#     assert not (deployed_repo / "files" / ".toremove").exists()
#     assert not (tmp_home / ".toremove").is_symlink()
#     assert (tmp_home / ".toremove").is_file()  # Original restored
#
#
# def test_vacate_command(deployed_repo: Path, runner: CliRunner, tmp_home: Path) -> None:
#     """Test vacating the entire deployment"""
#     # Setup managed file
#     test_file = tmp_home / ".vacate_test"
#     test_file.write_text("data")
#     runner.invoke(cli, ["add", str(test_file)])
#
#     # Verify symlink exists
#     assert (tmp_home / ".vacate_test").is_symlink()
#
#     # Vacate deployment
#     result = runner.invoke(cli, ["vacate"])
#     assert result.exit_code == 0
#
#     # Verify symlinks removed
#     assert not (tmp_home / ".vacate_test").is_symlink()
#     assert (tmp_home / ".vacate_test").is_file()
#
#     # Verify state cleared
#     state_file = Path(click.get_app_dir("tdm")) / "state"
#     assert not state_file.exists()
#
#
# def test_fork_directory(deployed_repo: Path, runner: CliRunner, tmp_home: Path) -> None:
#     """Test forking an entire directory"""
#     # Setup directory
#     test_dir = tmp_home / ".appconfig"
#     test_dir.mkdir()
#     (test_dir / "config.toml").write_text("settings")
#     runner.invoke(cli, ["add", str(test_dir)])
#
#     # Fork directory
#     result = runner.invoke(cli, ["fork", str(test_dir), "--profile=dev"])
#     assert result.exit_code == 0
#
#     # Verify fork metadata
#     fork_meta = deployed_repo / "forks" / "dev" / ".forked_dirs"
#     assert ".appconfig" in fork_meta.read_text()
#
#     # Verify directory symlink
#     assert (tmp_home / ".appconfig").is_symlink()
#     assert "forks/dev" in os.readlink(tmp_home / ".appconfig")
#
#     # Verify contents
#     assert (deployed_repo / "forks" / "dev" / ".appconfig" / "config.toml").exists()
