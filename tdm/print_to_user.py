import sys


def error(msg: str) -> None:
    print("\033[91mError\033[0m: " + msg, file=sys.stderr)  # noqa: T201
    sys.exit(1)


def success(msg: str) -> None:
    print("\033[92mSuccess\033[0m: " + msg)  # noqa: T201
    sys.exit(0)
