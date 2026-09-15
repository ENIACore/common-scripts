#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "bin" / "_lib"))
from formatting import (
    GREY,
    RESET,
    print_group_end,
    print_group_start,
    print_group_step,
)


def find_jdtls_pids() -> list[str]:
    own_pid = str(os.getpid())
    result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    pids = []
    for line in result.stdout.splitlines():
        if "org.eclipse.jdt.ls.core" in line:
            parts = line.split()
            if len(parts) > 1 and parts[1] != own_pid:
                pids.append(parts[1])
    return pids


def main() -> None:
    print_group_start("jdtls process killer")

    pids = find_jdtls_pids()
    if not pids:
        print_group_end("No jdtls processes found.", success=True)
        return

    for pid in pids:
        print_group_step(f"{GREY}Killing PID {pid}{RESET}")
        subprocess.run(["kill", "-9", pid])

    print_group_end(f"Killed {len(pids)} jdtls process(es).", success=True)


if __name__ == "__main__":
    main()
