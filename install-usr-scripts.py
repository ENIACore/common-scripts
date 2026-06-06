#!/usr/bin/env python3

import os
from pathlib import Path

HOME = Path.home()
USR_BIN = HOME / "bin"
LIB_DIR = USR_BIN / "_lib"
SCRIPTS_DIR = Path(__file__).parent.resolve()
ZSHRC = HOME / ".zshrc"

ZSHRC_BLOCK = """
# Add custom scripts directory to PATH
if [[ ':$PATH:' != *':$HOME/usr-bin:'* ]]; then
  export PATH="$HOME/usr-bin:$PATH"
fi
"""


def create_dirs():
    USR_BIN.mkdir(parents=True, exist_ok=True)
    LIB_DIR.mkdir(parents=True, exist_ok=True)
    # Make lib a package so scripts can do: from lib import mymodule
    init = LIB_DIR / "__init__.py"
    if not init.exists():
        init.touch()


def create_symlinks():
    for script in SCRIPTS_DIR.glob("*.py"):
        link = USR_BIN / script.stem  # strip .py
        link.unlink(missing_ok=True)
        link.symlink_to(script)


def modify_zshrc():
    zshrc_text = ZSHRC.read_text() if ZSHRC.exists() else ""
    if "usr-bin" in zshrc_text:
        print("PATH already configured in ~/.zshrc")
        return
    with ZSHRC.open("a") as f:
        f.write(ZSHRC_BLOCK)
    print("Added PATH update to ~/.zshrc")
    # Also export for the current process
    os.environ["PATH"] = f"{USR_BIN}:{os.environ.get('PATH', '')}"


def main():
    create_dirs()
    create_symlinks()
    modify_zshrc()
    print("Symlinks in ~/bin:")
    for p in sorted(USR_BIN.iterdir()):
        if p.name != "lib":
            print(f"  {p.name}")


if __name__ == "__main__":
    main()
