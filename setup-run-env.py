#!/usr/bin/env python3

import os
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


def setup_java() -> None:
    print_group_start("Java Setup")
    result = run_cmd("/usr/libexec/java_home -v 1.8", capture_output=True)
    java_home = result.stdout.strip()
    add_env_val("JAVA_HOME", java_home, "Java 1.8 home directory")
    print_group_step(f"JAVA_HOME → {java_home}")
    print_group_end("Java home set", success=True)


def setup_node() -> None:
    print_group_start("Node Setup (nvm use 12)")
    add_env_cmd("nvm use 12", "Ensure Node 12 is active")

    print_group_step("Creating /usr/local/bin if missing...")
    run_cmd("sudo mkdir -p /usr/local/bin")

    print_group_step("Symlinking npm and node into /usr/local/bin...")
    run_cmd('sudo ln -sf "$(which npm)" /usr/local/bin/npm')
    run_cmd('sudo ln -sf "$(which node)" /usr/local/bin/node')

    npm_link = run_cmd("ls -l /usr/local/bin/npm", capture_output=True).stdout.strip()
    node_link = run_cmd("ls -l /usr/local/bin/node", capture_output=True).stdout.strip()
    print_group_step(f"npm  → {npm_link}")
    print_group_step(f"node → {node_link}")
    print_group_end("npm and node symlinked", success=True)


def setup_python() -> None:
    print_group_start("Python 2.7.18 Setup")
    python_path = "/usr/local/bin/python"
    pyenv_python = f"{os.path.expanduser('~')}/.pyenv/versions/2.7.18/bin/python"

    run_cmd(f"sudo ln -sf {pyenv_python} {python_path}")
    add_env_val("PYTHON", python_path, "Python binary for npm/legacy tools")
    add_env_cmd(f'export PATH="$PATH:{python_path}"', "Add python 2.7.18 to PATH")

    py_link = run_cmd(f"ls -l {python_path}", capture_output=True).stdout.strip()
    print_group_step(f"python → {py_link}")
    print_group_end("Python 2.7.18 symlinked", success=True)


def setup_maven() -> None:
    print_group_start("Maven JVM Options")
    maven_opts = "-Xms4g -Xmx12g -XX:+PrintFlagsFinal"
    add_env_val("MAVEN_OPTS", f'"{maven_opts}"', "Heap size for dp-* applications")
    print_group_step(f"MAVEN_OPTS → {maven_opts}")
    print_group_end("Maven opts set", success=True)


def main() -> None:
    clear_env()
    print_header("Environment Setup")
    setup_java()
    print()
    setup_node()
    print()
    setup_python()
    print()
    setup_maven()
    print_header("Setup Complete")
    print_warning(
        "Run `source ~/usr-bin/source-env` to apply all exports to your current session."
    )


if __name__ == "__main__":
    main()
