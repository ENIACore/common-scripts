#!/usr/bin/env python3

import shutil
import shlex
import subprocess
import venv
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
HOME = Path.home()
VENV_DIR = HOME / ".local" / "share" / "cli" / "venv"
VENV_BIN = VENV_DIR / "bin"
USER_BIN = HOME / ".local" / "bin"
ZSHRC = HOME / ".zshrc"
COMMANDS = (
    "env-dp-run",
    "env-dp-vim",
    "env-node-install",
    "creds",
    "note",
    "sql",
    "kill-jdtls",
    "live-reload",
    "run-mfe-stack",
    "stop-mfe-stack",
)
RESERVED_COMMANDS = set(COMMANDS) | {"java-v", "node-v", "python-v"}
LOCAL_SCRIPTS_DIR = PROJECT_DIR / "local"
LOCAL_LAUNCHER_DIR = VENV_DIR.parent / "local-bin"
LOCAL_MANIFEST = VENV_DIR.parent / "local-scripts.txt"
SHELL_INTEGRATION_SOURCE = PROJECT_DIR / "shell" / "cli-env.sh"
SHELL_INTEGRATION_TARGET = VENV_DIR.parent / "cli-env.sh"
PATH_BLOCK = """# Add user-installed Python scripts to PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  export PATH="$HOME/.local/bin:$PATH"
fi
"""
SHELL_BLOCK = """# Load CLI environment-switching functions
if [[ -f "$HOME/.local/share/cli/cli-env.sh" ]]; then
  source "$HOME/.local/share/cli/cli-env.sh"
fi
"""


def install_package() -> None:
    VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
    if not VENV_DIR.exists():
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)
    subprocess.run(
        [
            str(VENV_BIN / "python"),
            "-m",
            "pip",
            "install",
            "--editable",
            str(PROJECT_DIR),
        ],
        check=True,
    )


def install_commands() -> None:
    USER_BIN.mkdir(parents=True, exist_ok=True)
    for name in COMMANDS:
        target = USER_BIN / name
        target.unlink(missing_ok=True)
        target.symlink_to(VENV_BIN / name)


def install_shell_integration() -> None:
    shutil.copy2(SHELL_INTEGRATION_SOURCE, SHELL_INTEGRATION_TARGET)


def install_local_scripts() -> None:
    LOCAL_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    scripts = sorted(
        path
        for path in LOCAL_SCRIPTS_DIR.glob("*.py")
        if path.is_file() and path.name != "__init__.py"
    )
    named_scripts: dict[str, Path] = {}
    for script in scripts:
        command = script.stem.replace("_", "-")
        if command in RESERVED_COMMANDS:
            raise ValueError(f"Local script command conflicts with an installed command: {command}")
        if command in named_scripts:
            raise ValueError(f"Multiple local scripts resolve to command: {command}")
        named_scripts[command] = script

    previous_commands = (
        set(LOCAL_MANIFEST.read_text().splitlines())
        if LOCAL_MANIFEST.exists()
        else set()
    )
    current_commands = set(named_scripts)
    LOCAL_LAUNCHER_DIR.mkdir(parents=True, exist_ok=True)
    for command in previous_commands - current_commands:
        launcher = LOCAL_LAUNCHER_DIR / command
        launcher.unlink(missing_ok=True)
        link = USER_BIN / command
        if link.is_symlink() and link.resolve(strict=False) == launcher:
            link.unlink()

    for command, script in named_scripts.items():
        launcher = LOCAL_LAUNCHER_DIR / command
        link = USER_BIN / command
        if link.is_symlink() and link.resolve(strict=False) == launcher:
            pass
        elif link.exists() or link.is_symlink():
            raise FileExistsError(f"Refusing to overwrite existing command: {link}")

        launcher.write_text(
            "#!/bin/sh\n"
            f"exec {shlex.quote(str(VENV_BIN / 'python'))} "
            f"{shlex.quote(str(script.resolve()))} \"$@\"\n",
            encoding="utf-8",
        )
        launcher.chmod(0o755)
        if not link.is_symlink():
            link.symlink_to(launcher)

    LOCAL_MANIFEST.write_text(
        "".join(f"{command}\n" for command in sorted(current_commands)),
        encoding="utf-8",
    )


def configure_path() -> None:
    text = ZSHRC.read_text() if ZSHRC.exists() else ""
    if "Add user-installed Python scripts to PATH" not in text:
        text = text.rstrip() + "\n\n" + PATH_BLOCK
    if "Load CLI environment-switching functions" not in text:
        text = text.rstrip() + "\n\n" + SHELL_BLOCK
    ZSHRC.write_text(text)


def main() -> None:
    install_package()
    install_commands()
    install_local_scripts()
    install_shell_integration()
    configure_path()
    print(f"Installed commands into {USER_BIN}")
    print("Open a new terminal or run: source ~/.zshrc")
    print("Environment changes can be applied with: source ~/.cliutils/source-env")


if __name__ == "__main__":
    main()
