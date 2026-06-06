#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "bin" / "_lib"))
from common import add_env_cmd, add_env_val, clear_env, run_cmd
from formatting import (
    print_group_end,
    print_group_start,
    print_group_step,
    print_header,
    print_warning,
)


def setup_node_18() -> None:
    print_group_start("Node Setup (nvm use 18)")
    add_env_cmd("nvm use 18", "Ensure Node 18 is active")
    print_group_end("Node 18 active", success=True)


def setup_java_26() -> None:
    print_group_start("Java Setup")
    result = run_cmd("/usr/libexec/java_home -v 26", capture_output=True)
    java_home = result.stdout.strip()
    add_env_val("JAVA_HOME", java_home, "Java 26 home directory")
    print_group_step(f"JAVA_HOME → {java_home}")
    print_group_end("Java home set", success=True)


def main() -> None:
    clear_env()
    print_header("Environment Setup")
    setup_node_18()
    print()
    setup_java_26()
    print_header("Setup Complete")
    print_warning(
        "Run `source ~/usr-bin/source-env` to apply all exports to your current session."
    )


if __name__ == "__main__":
    main()
