#!/usr/bin/env python3

import os
import signal
import subprocess
import sys

from cliutils.formatting import (
    GREY,
    RED,
    RESET,
    print_group_end,
    print_group_start,
    print_group_step,
)

PROCESS_PATTERN = "org.eclipse.jdt.ls.core"


def find_jdtls_pids() -> list[int]:
    result = subprocess.run(
        ["pgrep", "-f", PROCESS_PATTERN],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 1:
        return []
    result.check_returncode()
    own_pid = os.getpid()
    pids: list[int] = []
    for line in result.stdout.splitlines():
        if line:
            pid = int(line)
            if pid != own_pid:
                pids.append(pid)
    return pids


def main() -> int:
    print_group_start("jdtls process killer")

    try:
        pids = find_jdtls_pids()
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print_group_end(f"Could not find jdtls processes: {error}", success=False)
        return 1

    if not pids:
        print_group_end("No jdtls processes found.", success=True)
        return 0

    killed = 0
    already_exited = 0
    failures = 0
    for pid in pids:
        print_group_step(f"{GREY}Killing PID {pid}{RESET}")
        try:
            os.kill(pid, signal.SIGKILL)
            killed += 1
        except ProcessLookupError:
            print_group_step(f"{GREY}PID {pid} already exited{RESET}")
            already_exited += 1
        except PermissionError as error:
            print_group_step(f"{RED}Could not kill PID {pid}: {error}{RESET}")
            failures += 1

    if failures:
        print_group_end(
            f"Killed {killed}; failed to kill {failures} jdtls process(es).",
            success=False,
        )
        return 1
    result = f"Killed {killed} jdtls process(es)"
    if already_exited:
        result += f"; {already_exited} had already exited"
    print_group_end(result + ".", success=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
