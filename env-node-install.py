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

PYENV_ROOT = Path.home() / ".pyenv" / "versions"
PYTHON_VERSION = "3.11.9"


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
    print_group_start(f"Python {PYTHON_VERSION} Setup")
    pyenv_python = PYENV_ROOT / PYTHON_VERSION / "bin" / "python3"

    if not pyenv_python.exists():
        print_group_end(
            f"pyenv version {PYTHON_VERSION} not found — run: pyenv install {PYTHON_VERSION}",
            success=False,
        )
        sys.exit(1)

    run_cmd(f"sudo ln -sf {pyenv_python} /usr/local/bin/python3")
    run_cmd(f"sudo ln -sf {pyenv_python} /usr/local/bin/python")
    add_env_val("PYTHON", str(pyenv_python), f"Python {PYTHON_VERSION} binary")

    py_link = run_cmd(
        "ls -l /usr/local/bin/python3", capture_output=True
    ).stdout.strip()
    print_group_step(f"python3 → {py_link}")
    print_group_end(f"Python {PYTHON_VERSION} symlinked", success=True)


def main() -> None:
    clear_env()
    print_header(f"env-node-run  |  Node 12 + Python {PYTHON_VERSION}")
    setup_node()
    print()
    setup_python()
    print_header("Setup Complete")
    print_warning(
        "Run `source ~/bin/source-env` to apply all exports to your current session."
    )


if __name__ == "__main__":
    main()
