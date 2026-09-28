#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

from cliutils.formatting import (
    GREEN,
    GREY,
    RESET,
    YELLOW,
    get_group_input,
    print_group_end,
    print_group_start,
    print_group_step,
    run_cmd,
)
from cliutils.shell_env import (
    add_env_val,
    clear_env,
)

PYENV_ROOT = Path.home() / ".pyenv" / "versions"
BREW_PYTHON_PREFIX = Path("/opt/homebrew/opt")  # Apple Silicon
BREW_PYTHON_PREFIX_INTEL = Path("/usr/local/opt")  # Intel

USR_LOCAL_BIN = Path("/usr/local/bin")


def get_python_target(python_version: str) -> Path:
    return USR_LOCAL_BIN / f"python-{python_version}"


def get_bin_target(python_target: Path, bin_name: str) -> Path:
    return python_target / bin_name


def find_pyenv_python(version: str) -> Path | None:
    """Return the python binary path for a pyenv version, or None if not installed."""
    candidate = PYENV_ROOT / version / "bin" / "python3"
    if candidate.exists():
        return candidate
    # Some builds only have `python` not `python3`
    fallback = PYENV_ROOT / version / "bin" / "python"
    if fallback.exists():
        return fallback
    return None


def find_brew_python(version: str) -> Path | None:
    """Return the Homebrew python binary for the given major.minor version, or None."""
    major_minor = ".".join(version.split(".")[:2])
    formula = f"python@{major_minor}"
    for prefix in (BREW_PYTHON_PREFIX, BREW_PYTHON_PREFIX_INTEL):
        candidate = prefix / formula / "bin" / f"python{major_minor}"
        if candidate.exists():
            return candidate
        # Fallback: plain python3 binary in the formula bin dir
        candidate_plain = prefix / formula / "bin" / "python3"
        if candidate_plain.exists():
            return candidate_plain
    return None


def symlink_python(python_path: Path, python_target: Path) -> None:
    """Symlink python3 and python into the versioned target dir."""
    for name in ("python3", "python"):
        target = get_bin_target(python_target, name)
        run_cmd(f"sudo ln -sf {python_path} {target}")


def main() -> None:
    # ── Main ──────────────────────────────────────────────────────────────────────

    print()
    print_group_start("Python Version Switcher")
    print_group_step(
        f"{GREY}Enter a version installed in pyenv or via Homebrew (e.g. 2.7.18, 3.11.9, 3.12.4){RESET}"
    )
    print_group_step("")
    version = get_group_input("Input Python version")

    # ── 1. Try pyenv ──────────────────────────────────────────────────────────────
    python_path = find_pyenv_python(version)
    source = "pyenv"

    # ── 2. Fall back to Homebrew ──────────────────────────────────────────────────
    if python_path is None:
        print_group_step(
            f"{YELLOW}pyenv version '{version}' not found — checking Homebrew…{RESET}"
        )
        python_path = find_brew_python(version)
        source = "homebrew"

    # ── 3. Neither found ─────────────────────────────────────────────────────────
    if python_path is None:
        print_group_end(f"Python {version} not found in pyenv or Homebrew", success=False)
        print_group_step(f"{GREY}  pyenv install {version}{RESET}")
        print_group_step(
            f"{GREY}  brew install python@{'.'.join(version.split('.')[:2])}{RESET}"
        )
        sys.exit(1)

    print_group_step(f"Found via {GREEN}{source}{RESET}: {GREEN}{python_path}{RESET}")
    print_group_step("")

    # ── Symlink into /usr/local/bin ───────────────────────────────────────────────
    python_target = get_python_target(version)
    run_cmd(f"sudo mkdir -p {python_target}")
    symlink_python(python_path, python_target)

    # ── Verify ────────────────────────────────────────────────────────────────────
    python3_bin = get_bin_target(python_target, "python3")
    try:
        resolved_version = (
            subprocess.check_output(
                [str(python3_bin), "--version"], stderr=subprocess.STDOUT
            )
            .decode()
            .strip()
        )
        print_group_step(f"python3 → {GREEN}{resolved_version}{RESET}")
    except Exception:
        print_group_step(
            f"{YELLOW}Could not verify python3 version after symlinking{RESET}"
        )

    print_group_end(f"python / python3 → {python_path}  {GREY}(via {source}){RESET}")

    clear_env()
    add_env_val(
        "PATH",
        f"{python_target}:$PATH",
        f"Ensures python symlinks found in {python_target} are first in path",
        auto_source=True,
    )


if __name__ == "__main__":
    main()
