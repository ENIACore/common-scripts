#!/usr/bin/env python3

import base64
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from cliutils.clipboard import copy_to_clipboard
from cliutils.formatting import (
    GREEN,
    RED,
    RESET,
    get_group_input,
    get_group_password,
    print_group_end,
    print_group_start,
    print_group_step,
)
from cliutils.json_store import load_json, save_json
from cliutils.record_cli import choose_item

CREDS_PATH = Path("~/.local/state/cli/credentials.json").expanduser()
Credentials = dict[str, dict[str, str]]


def load_credentials() -> Credentials:
    credentials: Any = load_json(CREDS_PATH, default={})
    if not isinstance(credentials, dict):
        raise ValueError(f"Expected a JSON object at {CREDS_PATH}")
    for title, entry in credentials.items():
        if (
            not isinstance(title, str)
            or not isinstance(entry, dict)
            or not isinstance(entry.get("username"), str)
            or not isinstance(entry.get("password"), str)
        ):
            raise ValueError(f"Invalid credential entry for {title!r}")
    return credentials


def add_credential(credentials: Credentials) -> int:
    print()
    print_group_start("Add credentials")
    title = get_group_input("Title").strip()
    username = get_group_input("Username").strip()
    password = get_group_password("Password")
    if not title or not username or not password:
        print_group_end("Title, username, and password are required.", success=False)
        return 1
    if title in credentials:
        print_group_end(f"Credentials titled {title!r} already exist.", success=False)
        return 1

    credentials[title] = {"username": username, "password": password}
    save_json(CREDS_PATH, credentials)
    print_group_end(f"Saved credentials as {title!r}.")
    return 0


def get_credential(credentials: Credentials) -> int:
    if not credentials:
        print_group_start("No credentials saved")
        print_group_end("Use 'creds add' to create an entry.", success=False)
        return 1

    title = choose_item("Select credentials", sorted(credentials, key=str.casefold))
    if title is None:
        return 1

    username = credentials[title]["username"]
    password = credentials[title]["password"]
    encoded = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode(
        "ascii"
    )

    print()
    print_group_start(f"Credentials: {title}")
    print_group_step(f"Username: {GREEN}{username}{RESET}")
    print_group_step(f"Password: {RED}{password}{RESET}")
    print_group_step(f"Base64: {GREEN}{encoded}{RESET}")
    copied = copy_to_clipboard(password)
    if copied:
        print_group_end(f"Password copied to clipboard via {copied}.")
        return 0
    print_group_end(
        "Could not copy the password: install pbcopy, xclip, xsel, or wl-copy.",
        success=False,
    )
    return 1


def delete_credential(credentials: Credentials) -> int:
    if not credentials:
        print_group_start("No credentials saved")
        print_group_end("Nothing to delete.", success=False)
        return 1

    title = choose_item(
        "Select credentials to delete", sorted(credentials, key=str.casefold)
    )
    if title is None:
        return 1
    confirmation = get_group_input(f"Delete credentials {title!r}? (y/N)", "N")
    if confirmation.lower() != "y":
        print_group_end("Deletion cancelled.")
        return 0

    del credentials[title]
    save_json(CREDS_PATH, credentials)
    print_group_end(f"Deleted credentials {title!r}.")
    return 0


def usage() -> None:
    print("\n  Usage: creds add | get | delete")
    print("    creds add       # add credentials")
    print("    creds get       # display credentials and copy the password")
    print("    creds delete    # delete credentials\n")


def main(argv: Sequence[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv
    action = args[1].lower() if len(args) > 1 else ""
    if action in ("-h", "--help", "help"):
        usage()
        return 0
    if action not in {"add", "get", "delete"}:
        usage()
        return 2

    credentials = load_credentials()
    if action == "add":
        return add_credential(credentials)
    if action == "delete":
        return delete_credential(credentials)
    return get_credential(credentials)


if __name__ == "__main__":
    sys.exit(main())
