#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "usr-bin" / "_lib"))
from formatting import (
    GREEN,
    GREY,
    RESET,
    YELLOW,
    add_env_cmd,
    get_group_input,
    print_group_end,
    print_group_start,
    print_group_step,
    run_cmd,
)

PYENV_ROOT = Path.home() / ".pyenv" / "versions"
BREW_PYTHON_PREFIX = Path("/opt/homebrew/opt")  # Apple Silicon; Intel is /usr/local/opt
BREW_PYTHON_PREFIX_INTEL = Path("/usr/local/opt")

PYTHON_BIN = Path("/usr/local/bin/python3")
PYTHON_LEGACY_BIN = Path("/usr/local/bin/python")


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
    # Homebrew formula names: python@3.11, python@3.12, etc.
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


def symlink_python(python_path: Path) -> None:
    """Symlink /usr/local/bin/python3 and /usr/local/bin/python to python_path."""
    for target in (PYTHON_BIN, PYTHON_LEGACY_BIN):
        run_cmd(f"sudo ln -sf {python_path} {target}")


print()
print_group_start("Python Version Switcher")
print_group_step(
    f"{GREY}Enter a version installed in pyenv or via Homebrew (e.g. 3.11, 3.12.4){RESET}"
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
symlink_python(python_path)

# ── Verify ────────────────────────────────────────────────────────────────────
try:
    resolved_version = (
        subprocess.check_output(
            [str(PYTHON_BIN), "--version"], stderr=subprocess.STDOUT
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
