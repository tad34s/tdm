import io
from pathlib import Path

import pytest
from click.testing import CliRunner

from tdm.cli import cli
from tdm.tests.utils import File, assert_result, check_files, file_tree

FILES: list[File] = [
    File(path=Path(x), contents=y)
    for x, y in [
        (".config/nvim/lua/user/remaps.lua", 'My remaps: \n vim vim.g.mapleader = " "'),
        (".config/nvim/lua/user/opts.lua", "My ops"),
        (".config/picom.conf", "# My picom config"),
        (".config/polybar/config.ini", "# polybar config"),
        (".config/polybar/launch.sh", "# polybar script config"),
        (".config/rofi/scripts/ignored_file", ""),
        (".config/rofi/scripts/launcher", "rofi launcher"),
        (".config/rofi/scripts/menu", "rofi menu"),
        (".bashrc", "echo hello from bashrc"),
        (".config/nvim/.lazy-lock.json", "{}"),
        (".gitconfig", "# git config"),
    ]
]


FILES2: list[File] = [
    File(path=Path(x), contents=y)
    for x, y in [
        (".config/nvim/lua/user/remaps.lua", "remaps"),
        (".config/nvim/lua/user/opts.lua", "ops ops"),
        (".config/polybar/config.ini", "# polybar config"),
        (".config/polybar/launch.sh", "# polybar script config"),
        (".bashrc", "different bashrc"),
        (".config/nvim/.lazy-lock.json", "{}"),
        (".gitconfig", "# git config"),
    ]
]

sample_config = """
bootstrap = ""  # no script

# files or directories to ignore when adding a whole repository
ignore = [ 
    ".lazy-lock.json",
    "ignored_file"
]

# files or directories that are in the files.toml but we do not want to symlink them
exclude = [".gitconfig"]

[linux-dev]   
bootstrap = "linux.sh"  # overriding
include = [".gitconfig"] # overriding exclusion

[linux-dev-notebook]   
bootstrap = "linux.sh"  # overriding
include = [".gitconfig"] # overriding exclusion

[mac]
bootstrap = "mac.sh"   # overriding
exclude = ["picom.conf"] # adding to exclusion

[server] 
use-only = [  # if specifies will only use files or directories provided here
    "nvim"
]
"""


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
    for file in FILES:
        new_file = home / file.path
        new_file.parent.mkdir(exist_ok=True, parents=True)
        with new_file.open("w") as f:
            f.write(file.contents)
    print("Starting home:")
    print(file_tree(home))
    return home


@pytest.fixture
def tdm_prepped_repo(tmp_home: Path, runner: CliRunner) -> Path:
    """Initialize a new TDM repository"""
    repo = tmp_home / "dotfiles2"
    input_stream = io.StringIO("\n")  # Simulates pressing Enter
    result = runner.invoke(cli, ["init", "--git", str(repo)], input="\n")
    assert_result(result, "Init", tmp_home)
    (repo / "config.toml").write_text(sample_config)

    files_dir = repo / "files"

    bashrc = files_dir / ".bashrc"
    bashrc.write_text("# Sample bash config")

    nvim = files_dir / ".config" / "nvim"
    nvim.mkdir(parents=True)
    remaps = nvim / "lua/user/remaps.lua"
    remaps.parent.mkdir(parents=True)
    remaps.touch()

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


@pytest.fixture()
def used_repo(tmp_home: Path, runner: CliRunner):
    repo = tmp_home / "dotfiles"

    result = runner.invoke(cli, ["init", str(repo)])
    assert_result(result, "Init")
    (repo / "config.toml").write_text(sample_config)

    result = runner.invoke(cli, ["deploy", str(repo)])
    assert_result(result, "Deploy")

    to_add = [
        tmp_home / ".config/nvim",
        tmp_home / ".config/polybar",
        tmp_home / ".config/picom.conf",
        tmp_home / ".config/rofi",
        tmp_home / ".bashrc",
    ]

    for file_to_add in to_add:
        result = runner.invoke(cli, ["add", str(file_to_add)])
        assert_result(result, "Add")

    print("\nAfter tdm use:")
    print(file_tree(tmp_home))

    assert (tmp_home / ".bashrc").is_symlink(), ".bashrc is not symlink"
    assert (tmp_home / ".config/picom.conf").is_symlink(), "picomf.conf is not symlink"
    assert (tmp_home / ".config/polybar").is_symlink(), "picomf.conf is not symlink"
    assert not (tmp_home / ".config/nvim").is_symlink(), "nvim is a symlink"

    bootstrap_script = repo / "bin" / "linux.sh"
    bootstrap_script.write_text("#!/bin/bash\ntouch ~/bootstrap_ran_linux")
    bootstrap_script.chmod(0o755)

    check_files(FILES, tmp_home)

    return repo


@pytest.fixture
def additional_dotfiles(tmp_home: Path, runner: CliRunner):
    repo = tmp_home / "teckafiles"

    result = runner.invoke(cli, ["init", str(repo)])
    assert result.exit_code == 0, f"Init failed: {result.output}"
    (repo / "config.toml").write_text(sample_config)

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

    check_files(FILES, tmp_home)

    return repo
