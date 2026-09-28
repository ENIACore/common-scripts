import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from cliutils.clipboard import copy_to_clipboard
from cliutils.formatting import (
    BOLD,
    CYAN,
    GREY,
    RESET,
    get_group_input,
    print_group_end,
    print_group_start,
    print_group_step,
)
from cliutils.json_store import load_json, save_json

RecordStore = dict[str, dict[str, dict[str, Any]]]
LineFormatter = Callable[[list[str]], list[str]]
LineValidator = Callable[[list[str]], str | None]
GetHandler = Callable[[str, str, dict[str, Any]], int]


def load_records(path: Path) -> RecordStore:
    records = load_json(path, default={})
    if not isinstance(records, dict):
        raise ValueError(f"Expected a JSON object at {path}")

    for subject, titles in records.items():
        if not isinstance(subject, str) or not isinstance(titles, dict):
            raise ValueError(f"Invalid subject entry in {path}")
        for title, entry in titles.items():
            if (
                not isinstance(title, str)
                or not isinstance(entry, dict)
                or not isinstance(entry.get("description"), str)
                or not isinstance(entry.get("lines"), list)
                or not all(isinstance(line, str) for line in entry["lines"])
            ):
                raise ValueError(f"Invalid record for {subject!r}/{title!r}")
    return records


def choose_item(prompt: str, items: list[str]) -> str | None:
    print()
    print_group_start(prompt)
    for index, item in enumerate(items, start=1):
        print_group_step(f"{GREY}{index}.{RESET} {item}")
    print_group_step()

    choice = get_group_input("Enter a number, or q to cancel")
    if choice.lower() == "q" or not choice:
        print_group_end()
        return None
    if choice.isdigit() and 1 <= int(choice) <= len(items):
        selected = items[int(choice) - 1]
        print_group_end()
        return selected

    print_group_end(f"Invalid selection: {choice}", success=False)
    return None


def _add_record(
    path: Path,
    records: RecordStore,
    label: str,
    line_prompt: str,
    validate_lines: LineValidator | None,
) -> int:
    print()
    print_group_start(f"Add {label}")
    subject = get_group_input("Subject").strip()
    title = get_group_input("Title").strip()
    description = get_group_input("Description").strip()
    if not subject or not title or not description:
        print_group_end("Subject, title, and description are required.", success=False)
        return 1
    if title in records.get(subject, {}):
        print_group_end(
            f"A record titled {title!r} already exists under {subject!r}.",
            success=False,
        )
        return 1

    print_group_step(line_prompt)
    lines: list[str] = []
    while True:
        line = input("    ")
        if line == ".":
            break
        lines.append(line)

    if validate_lines is not None:
        validation_error = validate_lines(lines)
        if validation_error:
            print_group_end(validation_error, success=False)
            return 1

    records.setdefault(subject, {})[title] = {
        "description": description,
        "lines": lines,
    }
    save_json(path, records)
    print_group_end(f"Saved {title!r} under {subject!r}.")
    return 0


def _get_record(
    records: RecordStore,
    label: str,
    format_lines: LineFormatter,
    content_heading: str,
    get_handler: GetHandler | None,
) -> int:
    if not records:
        print_group_start(f"No {label} entries saved")
        print_group_end("Use the add option to create one.", success=False)
        return 1

    subjects = sorted(records, key=str.casefold)
    subject = choose_item("Select a subject", subjects)
    if subject is None:
        return 1
    titles = sorted(records[subject], key=str.casefold)
    if not titles:
        print_group_start("No entries in this subject")
        print_group_end(subject, success=False)
        return 1

    title = choose_item(f"Select a title in {subject}", titles)
    if title is None:
        return 1

    entry = records[subject][title]
    print()
    print_group_start(f"{subject}: {title}")
    print_group_step(f"{BOLD}Description:{RESET} {entry['description']}")
    print_group_step(f"{BOLD}{content_heading}:{RESET}")
    for line in format_lines(entry["lines"]):
        print_group_step(f"{CYAN}{line}{RESET}")

    if get_handler is not None:
        return get_handler(subject, title, entry)

    copied = copy_to_clipboard("\n".join(entry["lines"]))
    if copied:
        print_group_end(f"Copied content to clipboard via {copied}.")
        return 0
    print_group_end(
        "Could not copy: install pbcopy, xclip, xsel, or wl-copy.",
        success=False,
    )
    return 1


def _delete_record(path: Path, records: RecordStore, label: str) -> int:
    if not records:
        print_group_start(f"No {label} entries saved")
        print_group_end("Nothing to delete.", success=False)
        return 1

    subjects = sorted(records, key=str.casefold)
    subject = choose_item("Select a subject", subjects)
    if subject is None:
        return 1
    titles = sorted(records[subject], key=str.casefold)
    if not titles:
        print_group_start("No entries in this subject")
        print_group_end(subject, success=False)
        return 1

    title = choose_item(f"Select a title in {subject}", titles)
    if title is None:
        return 1

    confirmation = get_group_input(f"Delete {title!r} from {subject!r}? (y/N)", "N")
    if confirmation.lower() != "y":
        print_group_end("Deletion cancelled.")
        return 0

    del records[subject][title]
    if not records[subject]:
        del records[subject]
    save_json(path, records)
    print_group_end(f"Deleted {title!r} from {subject!r}.")
    return 0


def _list_records(records: RecordStore, label: str) -> int:
    if not records or not any(records.values()):
        print_group_start(f"No {label} entries saved")
        print_group_end("Use the add option to create one.", success=False)
        return 1

    print()
    print_group_start(f"Saved {label} entries")
    for subject in sorted(records, key=str.casefold):
        for title, entry in sorted(
            records[subject].items(), key=lambda item: item[0].casefold()
        ):
            print_group_step(f"{subject}: {title} - {entry['description']}")
    print_group_end()
    return 0


def run_record_command(
    command: str,
    label: str,
    path: Path,
    argv: Sequence[str] | None = None,
    format_lines: LineFormatter | None = None,
    action_descriptions: dict[str, str] | None = None,
    line_prompt: str = "Enter content one line at a time; enter a single '.' to finish.",
    validate_lines: LineValidator | None = None,
    content_heading: str = "Lines",
    get_handler: GetHandler | None = None,
) -> int:
    args = argv if argv is not None else sys.argv
    action = args[1].lower() if len(args) > 1 else ""
    if action in ("-h", "--help", "help"):
        descriptions = action_descriptions or {
            "add": f"add a {label} with a subject, title, description, and content lines",
            "get": f"select a subject and title, display the {label}, and copy its content",
            "delete": f"select a subject and title, then confirm deletion of the {label}",
            "list": f"list saved {label} entries",
        }
        print(f"\n{command}")
        print(f"\n  Usage: {command} add | get | list | delete")
        print(f"    {command} add       # {descriptions['add']}")
        print(f"    {command} get       # {descriptions['get']}")
        print(f"    {command} list      # {descriptions['list']}")
        print(f"    {command} delete    # {descriptions['delete']}\n")
        return 0
    if action not in {"add", "delete", "get", "list"}:
        print(f"Usage: {command} add | get | list | delete")
        return 2

    records = load_records(path)
    if action == "add":
        return _add_record(path, records, label, line_prompt, validate_lines)
    if action == "delete":
        return _delete_record(path, records, label)
    if action == "list":
        return _list_records(records, label)
    return _get_record(
        records,
        label,
        format_lines or (lambda lines: lines),
        content_heading,
        get_handler,
    )
