import sys


def error(msg: str, exit=True) -> None:
    if exit:
        print("\033[91mError\033[0m: " + msg, file=sys.stderr)  # noqa: T201
        sys.exit(1)
    else:
        print(f"\033[91m{msg}\033[0m: ", file=sys.stderr)  # noqa: T201


def success(msg: str) -> None:
    print("\033[92mSuccess\033[0m: " + msg)  # noqa: T201
    sys.exit(0)


def print_git(msg: str, error=False) -> None:
    indent = "  "
    if error:
        print("\033[91mError, git 󰊢\033[0m: " + msg, file=sys.stderr)  # noqa: T201
    else:
        print("\033[38;2;240;80;50mgit 󰊢\033[0m:")
        print(indent + msg.replace("\n", f"\n{indent}"))  # noqa: T201


def warning(msg: str, ask_continue: bool = False) -> None:
    print("\033[33mWarning\033[0m: " + msg)
    if ask_continue:
        output = input("Do you wish to continue? [y/N] ")
        if output.strip() == "y" or output.strip() == "yes":
            print()
            return
        else:
            sys.exit(2)
