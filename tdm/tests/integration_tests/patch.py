import shutil
from pathlib import Path

from click.testing import CliRunner

from tdm.cli import cli
from tdm.tests.fixtures import *
from tdm.tests.fixtures import FILES
from tdm.tests.utils import assert_result, check_files, file_tree

# NOTE: Patch
# Patch shoudl do all the following things
# - Add files that were added in an added directory
# - Remove ignored files that somehow ended up in a symlinked dir
# - Recalculate symlink structrure
#   - if some links were deleted, it will relink them


def test_patch(tmp_home: Path, used_repo: Path, runner: CliRunner):
    new_dir = tmp_home / ".config" / "nvim" / "plugins"
    new_dir.mkdir()
    (new_dir / "floaterminal.lua").touch()
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "Patch")
    print(file_tree(tmp_home))
    assert new_dir.is_symlink()


def test_patch_kickout_dir(tmp_home: Path, used_repo: Path, runner: CliRunner):
    new_dir = tmp_home / ".config/polybar"
    # assert_result(result, "Patch")
    (new_dir / ".lazy-lock.json").mkdir()
    (new_dir / ".lazy-lock.json" / "hi").touch()
    (new_dir / ".lazy-lock.json" / "hi2").touch()
    (new_dir / ".lazy-lock.json" / "hi3").mkdir()
    print(file_tree(tmp_home))
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "Patch", tmp_home)

    # now kickout where the target is populated somehow
    # testng if it can kickout directories
    (tmp_home / ".config/nvim/.lazy-lock.json").unlink()
    (tmp_home / ".config/nvim/.lazy-lock.json").mkdir()
    (tmp_home / ".config/nvim/.lazy-lock.json/hi").touch()

    (used_repo / "files" / ".config/nvim/.lazy-lock.json").mkdir()
    (used_repo / "files" / ".config/nvim/.lazy-lock.json/hi").touch()

    result = runner.invoke(cli, ["patch"])
    assert_result(result, "Patch", tmp_home)


def test_patch_with_ignore(tmp_home: Path, used_repo: Path, runner: CliRunner):
    new_dir = tmp_home / ".config" / "nvim" / "plugins"
    new_dir.mkdir()
    (new_dir / "floaterminal.lua").touch()
    (new_dir / ".lazy-lock.json").touch()
    result = runner.invoke(cli, ["patch"])
    # should recalculate the symlink structure correctly
    assert_result(result, "Patch")
    print(file_tree(tmp_home))
    assert not (new_dir).is_symlink()
    assert (new_dir / "floaterminal.lua").is_symlink()


def test_patch_new_ignore(tmp_home: Path, used_repo: Path, runner: CliRunner):
    new_dir = tmp_home / ".config" / "nvim" / "plugins"
    new_dir.mkdir()
    (new_dir / "floaterminal.lua").touch()
    (new_dir / "other_file").touch()
    result = runner.invoke(cli, ["patch"])

    assert (new_dir).is_symlink()
    # changin already added file to ignored files
    (new_dir / "other_file").rename(new_dir / ".lazy-lock.json")
    # should correctly recalculate the symlink structure
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


def test_patch_whole_dir_is_symlnked(tmp_home: Path, used_repo: Path, runner: CliRunner):
    ignored = tmp_home / ".config/nvim/.lazy-lock.json"
    ignored.unlink()
    assert not ignored.exists()
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "Patch")
    files = FILES.copy()
    files.remove(File(Path(".config/nvim/.lazy-lock.json"), "{}"))
    check_files(files, tmp_home)
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "Patch")


def test_patch_relinking_with_ignored(tmp_home: Path, used_repo: Path, runner: CliRunner):
    # symlinking whole neovim
    ignored = tmp_home / ".config/nvim/.lazy-lock.json"
    ignored.unlink()
    assert not ignored.exists()
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "Patch")
    files = FILES.copy()
    files.remove(File(Path(".config/nvim/.lazy-lock.json"), "{}"))
    check_files(files, tmp_home)
    result = runner.invoke(cli, ["patch"])
    assert_result(result, "Patch")

    # replacing symlink with actual files
    nv_dir = tmp_home / ".config/nvim"
    nv_dir_src = used_repo / "files" / ".config/nvim"
    nv_dir.unlink()
    shutil.copytree(nv_dir_src, nv_dir)

    # adding back ignore and patching
    ignored.touch()
    (nv_dir / "init.lua").touch()
    print(file_tree(tmp_home))

    result = runner.invoke(cli, ["patch"])
    assert_result(result, "Patch")
    print(file_tree(tmp_home))
