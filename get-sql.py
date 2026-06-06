#!/usr/bin/env python3

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "bin" / "_lib"))
from common import copy_to_clipboard
from formatting import (
    BOLD,
    GREEN,
    GREY,
    MAGENTA,
    RED,
    RESET,
    WHITE,
    YELLOW,
    get_group_input,
    print_group_end,
    print_group_start,
    print_group_step,
)

KEYWORD_COLOR = MAGENTA
STRING_COLOR = GREEN
NUMBER_COLOR = YELLOW
COMMENT_COLOR = WHITE

KEYWORDS = (
    "COUNT",
    "BY",
    "SELECT",
    "FROM",
    "WHERE",
    "JOIN",
    "LEFT",
    "RIGHT",
    "INNER",
    "OUTER",
    "FULL",
    "ON",
    "GROUP",
    "ORDER",
    "HAVING",
    "LIMIT",
    "OFFSET",
    "INSERT",
    "INTO",
    "VALUES",
    "UPDATE",
    "SET",
    "DELETE",
    "CREATE",
    "DROP",
    "ALTER",
    "TABLE",
    "INDEX",
    "VIEW",
    "AS",
    "AND",
    "OR",
    "NOT",
    "IN",
    "IS",
    "NULL",
    "LIKE",
    "BETWEEN",
    "EXISTS",
    "UNION",
    "ALL",
    "DISTINCT",
    "CASE",
    "WHEN",
    "THEN",
    "ELSE",
    "END",
    "WITH",
    "RETURNING",
    "INTERVAL",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "NOW",
    "ROUND",
    "COALESCE",
    "CAST",
    "DATE_TRUNC",
)

_TOKEN_RE = re.compile(
    r"(?P<comment>--[^\n]*)"
    r"|(?P<string>'[^']*')"
    r"|(?P<number>\b\d+(?:\.\d+)?\b)"
    r"|(?P<keyword>\b(?:" + "|".join(KEYWORDS) + r")\b)",
    re.IGNORECASE,
)
_COLOR_BY_GROUP = {
    "comment": COMMENT_COLOR,
    "string": STRING_COLOR,
    "number": NUMBER_COLOR,
    "keyword": KEYWORD_COLOR,
}

QUERIES = {
    "EXAMPLE-NAME": {
        "description": "Example description",
        "sql": [
            "SELECT *",
            "FROM EXAMPLE;",
        ],
    },
}

SQL_NAMES = list(QUERIES.keys())


def highlight_sql(line: str) -> str:
    def colorize(match: re.Match) -> str:
        kind = match.lastgroup
        if kind is None:
            return ""
        matched = match.group()
        if matched is None:
            return ""
        return f"{_COLOR_BY_GROUP[kind]}{matched}{RESET}"

    return _TOKEN_RE.sub(colorize, line)


def print_sql(name: str, sql: list[str]) -> None:
    print()
    print_group_start(f"SQL: {YELLOW}{name}{RESET}")
    for line in sql:
        highlighted_sql = highlight_sql(line)
        print_group_step(highlighted_sql)

    sql_str = "\n".join(sql)
    tool = copy_to_clipboard(sql_str)
    if tool:
        print_group_end(f"Copied to clipboard {GREY}(via {tool}){RESET}")
    else:
        print_group_end(
            "Could not copy — install pbcopy / xclip / xsel / wl-copy",
            success=False,
        )


def print_list() -> int:
    print()
    print_group_start("Available SQL queries")
    for i, name in enumerate(SQL_NAMES, 1):
        desc = QUERIES[name]["description"]
        print_group_step(
            f"{GREY}{i}.{RESET} {BOLD}{YELLOW}{name}{RESET}  {GREY}{desc}{RESET}"
        )
    print_group_step()
    choice: str = get_group_input(f"Enter a number to copy, or {GREY}q{RESET} to quit")
    if choice.lower() == "q" or choice == "":
        return -1
    if choice.isdigit() and 1 <= int(choice) <= len(SQL_NAMES):
        print_group_end()
        return int(choice)
    else:
        print_group_end(f"Invalid choice: {choice}", False)
        return -1


def main(argv: list[str]) -> int:
    arg = argv[1] if len(argv) > 1 else ""

    if arg in ("ls", "list", ""):
        choice: int = print_list()
        if choice == -1:
            return 1

        SQL_NAMES = list(QUERIES.keys())
        name = SQL_NAMES[choice]
        sql: list[str] = QUERIES[name]["sql"]
        print_sql(name, sql)
        return 0

    entry = QUERIES.get(arg)
    if entry is None:
        print()
        print_group_start("Error")
        print_group_step(f"{RED}Unknown query:{RESET} {BOLD}{arg}{RESET}")
        print_group_end(
            f"Run {BOLD}get-sql ls{RESET} to see available queries.", success=False
        )
        return 1

    print_sql(arg, entry["sql"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
