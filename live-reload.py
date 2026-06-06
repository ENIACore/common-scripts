#!/usr/bin/env python3

# @TODO@ - Redo, file is ai generated conversion from bash
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "bin" / "_lib"))
from formatting import (
    GREEN,
    RED,
    RESET,
    get_input,
    print_group_end,
    print_group_start,
    print_group_step,
)

print_group_start("Java Auto-Compiler")

version = get_input("Java version (number only, i.e 8, 11, 17, 26)")

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
    print_group_end(f"No JDK found for version {version}", success=False)
    sys.exit(1)

project_dir = get_input("Project directory")
project_path = Path(project_dir).expanduser().resolve()

if not project_path.exists():
    print_group_end(f"Directory not found: {project_dir}", success=False)
    sys.exit(1)

print_group_step(f"JAVA_HOME: {GREEN}{java_home}{RESET}")
print_group_step(f"Watching: {GREEN}{project_path}/src{RESET}")
print_group_end(f"Starting fswatch — press Ctrl+C to stop")

env = {**__import__("os").environ, "JAVA_HOME": java_home}

fswatch = subprocess.Popen(
    ["fswatch", "-o", str(project_path / "src")],
    stdout=subprocess.PIPE,
    env=env,
)

try:
    assert fswatch.stdout is not None
    for _ in fswatch.stdout:
        result = subprocess.run(
            ["mvn", "compile", "-q"],
            cwd=project_path,
            env=env,
        )
        if result.returncode == 0:
            print_group_step(f"{GREEN}✓ Compiled successfully{RESET}")
        else:
            print_group_step(f"{RED}✗ Compile failed{RESET}")
except KeyboardInterrupt:
    fswatch.terminate()
    print_group_end("Stopped")
