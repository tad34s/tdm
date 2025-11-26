from pathlib import Path


class SimulatedRepo:
    def __init__(self, name: str, managed_files: list[tuple[Path, str]]) -> None:
        self.files = list(File(path=x[0], contents=x[1]) for x in managed_files)
        self.name = name

    def check_files(self, home: Path):
        for file in self.files:
            real_file = home / file.path
            assert real_file.exists()
            assert real_file.read_text() == file.contents

    def create_repo(self, home: Path, runner):
        repo = home / self.name
        result = runner.invoke(cli, ["init", str(repo.resolve())])
        assert result.exit_code == 0, f"Init failed: {result.output}"
