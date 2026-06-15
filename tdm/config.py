import tomllib
from glob import escape
from pathlib import Path

from tdm.names import FILE_DIR_NAME
from tdm.print_to_user import error

DEFAULT_PROFILE_NAME = "base"


class Config:
    def __init__(
        self,
        exclude: list[str],
        ignore: list[str],
        use_only: list[Path],
        bootstrap: str | None,
    ) -> None:
        self.exclude: list[str] = exclude
        self.ignore: list[str] = ignore
        self.use_only: list[Path] = use_only
        self.bootstrap: str | None = bootstrap

        # NOTE: When we are using 'use_only' we already find the relative paths, because the logic is more complicated there and having the paths ready makes it easier (so that we do not mark the parents as excluded)

    @staticmethod
    def load(repo: Path, profile: str) -> "Config":
        with (repo / "config.toml").open("rb") as f:
            data = tomllib.load(f)
        exclude = data.get("exclude", [])
        ignore = data.get("ignore", [])
        use_only = data.get("use-only", [])
        bootstrap = data.get("bootstrap", "")
        bootstrap = bootstrap if bootstrap else None

        if profile == DEFAULT_PROFILE_NAME:
            return Config(exclude, ignore, use_only, bootstrap)

        profile_config = data.get(profile)
        if profile_config is None:
            error("Profile not found.")
            return Config([], [], [], bootstrap)  # unreachable, for linter :D

        for file in profile_config.get("exclude", []):
            exclude.append(file)

        for file in profile_config.get("include", []):
            exclude.remove(file)

        files_location = repo / FILE_DIR_NAME
        use_only = []
        for file in profile_config.get("use-only", []):
            matches = list(files_location.rglob(f"*{escape(file)}*"))
            for match in matches:
                relative_path = match.relative_to(files_location)
                use_only.append(relative_path)

        bootstrap = profile_config.get("bootstrap", bootstrap)
        bootstrap = bootstrap or None

        return Config(exclude, ignore, use_only, bootstrap)
