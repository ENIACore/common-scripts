#!/usr/bin/env python3

from pathlib import Path
from collections.abc import Sequence

from cliutils.record_cli import run_record_command

NOTES_PATH = Path("~/.local/state/cli/notes.json").expanduser()


def main(argv: Sequence[str] | None = None) -> int:
    return run_record_command(
        "note",
        "note",
        NOTES_PATH,
        argv,
        action_descriptions={
            "add": "add a note with a subject, title, description, and content lines",
            "get": "select a subject and title, display the note, and copy its content",
            "list": "list saved notes by subject and title",
            "delete": "select a subject and title, then confirm deletion of the note",
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
