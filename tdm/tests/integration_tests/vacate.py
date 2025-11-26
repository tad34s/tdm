from pathlib import Path

from click.testing import CliRunner

from tdm.cli import cli
from tdm.tests.fixtures import *
from tdm.tests.fixtures import FILES
from tdm.tests.utils import assert_result, check_files, file_tree


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
    assert_result(result, "vacate")
    i = [str(file.path) for file in FILES].index(".config/nvim/lua/user/remaps.lua")
    files = FILES.copy()
    files[i].contents = "echo Different remaps"
    check_files(files, tmp_home)
    print(file_tree(used_repo))
    i = [str(file.path) for file in files].index(".config/nvim/.lazy-lock.json")
    files.pop(i)
    i = [str(file.path) for file in files].index(".gitconfig")
    files.pop(i)

    i = [str(file.path) for file in files].index(".config/rofi/scripts/ignored_file")
    files.pop(i)
    check_files(files, used_repo / "files")
