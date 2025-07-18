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


def assert_result(result: Result, command_name: str, home: Path | None = None):
    print(f"Output:\n{result.output}")
    print(f"StdOut:\n{result.stdout}")
    print(f"StdErr:\n{result.stderr}")
    print(f"Exception:{result.exception}")
    tracebakc_ig: TracebackType = result.exc_info[2]
    print(traceback.print_tb(tracebakc_ig))
    if home:
        print("Tree after command: \n", file_tree(home))
    assert result.exit_code == 0, f"{command_name} failed\n"


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
    assert_result(result, "Init", tmp_home)

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
        assert result.exit_code == 0, "add failed\n"

    print("\nAfter tdm use:")
    print(file_tree(tmp_home))

    assert (tmp_home / ".bashrc").is_symlink(), ".bashrc is not symlink"
    assert (tmp_home / ".config/picom.conf").is_symlink(), "picomf.conf is not symlink"
    assert not (tmp_home / ".config/nvim").is_symlink(), "nvim is a symlink"

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

    print("symlinked dirs", (tmp_home / "dotfiles" / ".tdm" / "symlinked_dirs").read_text())

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
    assert result.exit_code == 0, f"Fork failed: {result.output}"

    (tmp_home / ".config/nvim/lua/user/remaps.lua").write_text("echo Different remaps")
    assert (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text() == "echo Different remaps"

    print("file_tree", file_tree(tmp_home))
    result = runner.invoke(cli, ["use", "base"])
    assert_result(result, "Use", tmp_home)

    assert (
        tmp_home / ".config/nvim/lua/user/remaps.lua"
    ).read_text() == 'My remaps: \n vim vim.g.mapleader = " "'

    result = runner.invoke(cli, ["use", "linux-dev", "-b"])
    assert result.exit_code == 0, f"Use failed: {result.output}"

    assert (tmp_home / ".config/nvim/lua/user/remaps.lua").read_text() == "echo Different remaps"


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
