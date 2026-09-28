#!/usr/bin/env python3

import subprocess
import sys
import time

from cliutils.formatting import (
    CYAN,
    GREEN,
    GREY,
    RED,
    RESET,
    YELLOW,
    get_group_input,
    print_group_end,
    print_group_start,
    print_group_step,
    print_header,
)
from cliutils.tmux import run_tmux

SESSION = "local-mfe"
GRACEFUL_WAIT = 3


def session_exists() -> bool:
    return run_tmux(["has-session", "-t", SESSION], check=False).returncode == 0


def get_windows() -> list[str]:
    r = run_tmux(["list-windows", "-t", SESSION, "-F", "#{window_name}"])
    return [w.strip() for w in r.stdout.splitlines() if w.strip()]


def send_interrupt(window: str) -> None:
    run_tmux(["send-keys", "-t", f"{SESSION}:{window}", "C-c", ""])
    time.sleep(GRACEFUL_WAIT)


def main() -> int:
    print_header("stop-local-mfe  |  graceful shutdown")

    try:
        if not session_exists():
            print_group_start("Session check")
            print_group_end(
                f"No tmux session named '{SESSION}' found — nothing to do.",
                success=True,
            )
            return 0

        windows = get_windows()

        print_group_start(f"Session '{SESSION}' found")
        for window in windows:
            print_group_step(f"{GREY}  {window}{RESET}")
        print_group_step()
        answer = get_group_input(
            f"{YELLOW}Interrupt all windows and destroy session?{RESET}  {GREY}(y/N){RESET}",
            default="N",
        )
        if answer.lower() != "y":
            print_group_end("Aborted.", success=False)
            return 0
        print_group_end("Proceeding with shutdown", success=True)
        print()

        print_group_start("Sending Ctrl-C to all windows")
        failures = 0
        for window in windows:
            print_group_step(
                f"{CYAN}{window:<20}{RESET} {GREY}sending Ctrl-C…{RESET}"
            )
            try:
                send_interrupt(window)
            except subprocess.CalledProcessError as error:
                detail = error.stderr.strip() if error.stderr else str(error)
                print_group_step(
                    f"{RED}Could not interrupt {window}: {detail}{RESET}"
                )
                failures += 1
            else:
                print_group_step(f"{GREEN}✓{RESET} {GREY}{window}{RESET}")
        if failures:
            print_group_end(
                f"Failed to interrupt {failures} window(s); keeping the session.",
                success=False,
            )
            return 1
        print_group_end("All windows interrupted", success=True)
        print()

        print_group_start(f"Destroying session '{SESSION}'")
        run_tmux(["kill-session", "-t", SESSION])
        print_group_end(f"Session '{SESSION}' destroyed", success=True)
        print()
        return 0
    except (OSError, subprocess.CalledProcessError) as error:
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            detail = error.stderr.strip()
        else:
            detail = str(error)
        print_group_start("Shutdown error")
        print_group_end(detail, success=False)
        return 1


if __name__ == "__main__":
    sys.exit(main())
