import tomllib
from pathlib import Path

from print_to_user import error

DEFAULT_PROFILE_NAME = "base"


class Config:
    def __init__(
        self,
        exclude: list[str],
        ignore: list[str],
        use_only: list[str] | None,
        bootstrap: str | None,
    ) -> None:
        self.exclude: list[str] = exclude
        self.ignore: list[str] = ignore
        self.use_only: list[str] | None = use_only
        self.bootstrap: str | None = bootstrap

    @staticmethod
    def load(repo: Path, profile: str) -> "Config":
        with (repo / "config.toml").open("rb") as f:
            data = tomllib.load(f)
        exclude = data.get("exclude", [])
        ignore = data.get("ignore", [])
        use_only = data.get("use-only")
        bootstrap = data.get("bootstrap", "")
        bootstrap = bootstrap if bootstrap else None

        if profile == DEFAULT_PROFILE_NAME:
            return Config(exclude, ignore, use_only, bootstrap)

        profile_config = data.get(profile)
        if profile_config is None:
            error("Profile not found.")
            return Config([], [], None, bootstrap)  # unreachable, for linter :D

        for file in profile_config.get("exclude", []):
            exclude.append(file)

        for file in profile_config.get("include", []):
            exclude.remove(file)

        use_only = data.get("use-only")
        bootstrap = data.get("bootstrap", bootstrap)
        bootstrap = bootstrap if bootstrap else None

        return Config(exclude, ignore, use_only, bootstrap)
