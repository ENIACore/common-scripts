#!/usr/bin/env python3

from collections.abc import Sequence
from pathlib import Path

from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import SqlLexer

from cliutils.record_cli import run_record_command

SQL_PATH = Path("~/.local/state/cli/sql.json").expanduser()


def highlight_sql_lines(lines: list[str]) -> list[str]:
    if not lines:
        return []
    source = "\n".join(lines)
    highlighted = highlight(
        source,
        SqlLexer(stripnl=False, ensurenl=False),
        Terminal256Formatter(style="monokai"),
    )
    if highlighted.endswith("\n"):
        highlighted = highlighted[:-1]
    return highlighted.split("\n")


def main(argv: Sequence[str] | None = None) -> int:
    return run_record_command(
        "sql",
        "SQL query",
        SQL_PATH,
        argv,
        highlight_sql_lines,
        action_descriptions={
            "add": "add a query with a subject, title, description, and SQL lines",
            "get": "select a subject and title, display highlighted SQL, and copy it",
            "list": "list saved queries by subject and title",
            "delete": "select a subject and title, then confirm deletion of the query",
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
