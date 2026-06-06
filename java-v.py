#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "bin" / "_lib"))
from common import add_env_val, clear_env
from formatting import (
    GREY,
    RESET,
    get_group_input,
    print_group_end,
    print_group_start,
    print_group_step,
)

print()
print_group_start("Java Version Switcher")
print_group_step(f"{GREY}Java Version Options (e.g. 1.8, 11, 17, 26){RESET}")
print_group_step("")
version = get_group_input("Input Java version")

try:
    java_home = (
        subprocess.check_output(
            ["/usr/libexec/java_home", "-v", version],
            stderr=subprocess.DEVNULL,
        )
        .decode()
        .strip()
    )
except subprocess.CalledProcessError:
    print_group_end(f"No JDK found for version {version}", False)
    sys.exit(1)

print_group_end(f"JAVA_HOME: {java_home}")
print()

clear_env()
add_env_val("JAVA_HOME", java_home, "Java JDK path to be used by maven and jdtls")
