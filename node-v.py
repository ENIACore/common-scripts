#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "bin" / "_lib"))
from common import add_env_val, clear_env, run_cmd
from formatting import (
    GREEN,
    GREY,
    RESET,
    YELLOW,
    get_group_input,
    print_group_end,
    print_group_start,
    print_group_step,
)

NVM_VERSIONS_ROOT = Path.home() / ".nvm" / "versions" / "node"
BREW_PREFIX = Path("/opt/homebrew/opt")  # Apple Silicon
BREW_PREFIX_INTEL = Path("/usr/local/opt")  # Intel

USR_LOCAL_BIN = Path("/usr/local/bin")


def get_node_target(node_version: str) -> Path:
    node_version = "node-" + node_version
    node_target = USR_LOCAL_BIN / node_version
    return node_target


def get_bin_target(node_target: Path, bin_name: str) -> Path:
    bin_target = node_target / bin_name
    return bin_target


BINARIES = [
    "node",
    "npm",
    "npx",
]


def _normalise_version(version: str) -> str:
    """Strip a leading 'v' so both 'v20.11.0' and '20.11.0' are accepted."""
    return version.lstrip("v")


def find_brew_node(version: str) -> Path | None:
    """Return the Homebrew node binary for the given major (or major.minor) version."""
    major = version.split(".")[0]
    formula = f"node@{major}"
    for prefix in (BREW_PREFIX, BREW_PREFIX_INTEL):
        candidate = prefix / formula / "bin" / "node"
        if candidate.exists():
            return candidate / ".." / ".."  # return the bin dir's parent (formula root)
    return None


def find_brew_node_bins(version: str) -> dict[str, Path] | None:
    """Return a dict of {name: path} for node/npm/npx under the Homebrew formula."""
    major = version.split(".")[0]
    formula = f"node@{major}"
    for prefix in (BREW_PREFIX, BREW_PREFIX_INTEL):
        bin_dir = prefix / formula / "bin"
        if (bin_dir / "node").exists():
            result = {}
            for name in BINARIES:
                p = bin_dir / name
                if p.exists():
                    result[name] = p
            return result if "node" in result else None
    return None


def find_nvm_node_bins(version: str) -> dict[str, Path] | None:
    """Return a dict of {name: path} for node/npm/npx under the NVM version dir."""
    # Support both 'v20.11.0' and '20.11.0'
    candidates = [f"v{version}", version]
    for version in candidates:
        bin_dir = NVM_VERSIONS_ROOT / version / "bin"
        if (bin_dir / "node").exists():
            result = {}
            for name in BINARIES:
                p = bin_dir / name
                if p.exists():
                    result[name] = p
            return result if "node" in result else None
    return None


def symlink_bins(bins: dict[str, Path], node_target: Path) -> None:
    """Symlink node, npm, and npx into /usr/local/bin."""
    for name in BINARIES:
        src = bins.get(name)
        target = get_bin_target(node_target, name)
        if src:
            run_cmd(f"sudo ln -sf {src} {target}")
        else:
            print_group_step(
                f"{YELLOW}'{name}' not found in version bin dir — skipping{RESET}"
            )


# ── Main ──────────────────────────────────────────────────────────────────────

print()
print_group_start("Node Version Switcher")
print_group_step(
    f"{GREY}Enter a Node version installed via Homebrew or nvm (e.g. v12.22.12, v18.20.8, v22.21.0){RESET}"
)
print_group_step("")
version = _normalise_version(get_group_input("Input Node version"))

# ── 1. Try Homebrew first ─────────────────────────────────────────────────────
bins = find_brew_node_bins(version)
source = "homebrew"

# ── 2. Fall back to NVM ───────────────────────────────────────────────────────
if bins is None:
    print_group_step(
        f"{YELLOW}Homebrew node@{version.split('.')[0]} not found — checking nvm…{RESET}"
    )
    bins = find_nvm_node_bins(version)
    source = "nvm"

# ── 3. Neither found ─────────────────────────────────────────────────────────
if bins is None:
    print_group_end(f"Node {version} not found via Homebrew or nvm", success=False)
    print_group_step(f"{GREY}  brew install node@{version.split('.')[0]}{RESET}")
    print_group_step(f"{GREY}  nvm install {version}{RESET}")
    sys.exit(1)

print_group_step(f"Found via {GREEN}{source}{RESET}:")
for name, path in bins.items():
    print_group_step(f"  {name} → {GREEN}{path}{RESET}")
print_group_step("")

# ── Symlink into /usr/local/bin ───────────────────────────────────────────────
node_target = get_node_target(version)
run_cmd(f"sudo mkdir -p {node_target}")
symlink_bins(bins, node_target)

# ── Verify ────────────────────────────────────────────────────────────────────
node_bin = get_bin_target(node_target, "node")
try:
    resolved = (
        subprocess.check_output([str(node_bin), "--version"], stderr=subprocess.STDOUT)
        .decode()
        .strip()
    )
    print_group_step(f"node → {GREEN}{resolved}{RESET}")
except Exception:
    print_group_step(f"{YELLOW}Could not verify node version after symlinking{RESET}")

print_group_end(
    f"node / npm / npx → {list(bins.values())[0].parent}  {GREY}(via {source}){RESET}"
)

clear_env()
add_env_val(
    "PATH",
    f"{node_target}:$PATH",
    f"Ensures node symlinks found in {node_target} are first in path",
)
