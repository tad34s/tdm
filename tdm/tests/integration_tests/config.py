from pathlib import Path

from click.testing import CliRunner

from tdm.cli import cli
from tdm.tests.fixtures import *
from tdm.tests.utils import assert_result, check_files, check_not_symlinked, check_symlinked


def test_use_only(tmp_home: Path, used_repo: Path, runner: CliRunner):

    result = runner.invoke(cli, ["use", "server"])

    assert_result(result, "Use to use-only", tmp_home)

    check_files(FILES, tmp_home)

    nvim_path = tmp_home / ".config" / "nvim" / "lua"
    check_symlinked([nvim_path])

    bin_path = tmp_home / "bin"
    check_symlinked([bin_path])

    paths_rest = [x.path for x in FILES if ("nvim" not in str(x.path) and "dev" not in str(x.path))]
    check_not_symlinked(paths_rest)
