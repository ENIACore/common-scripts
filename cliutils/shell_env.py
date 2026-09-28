from pathlib import Path

from cliutils.formatting import print_info, print_warning

CLIUTILS_STATE_DIR = Path("~/.cliutils").expanduser()
SOURCE_ENV_PATH = CLIUTILS_STATE_DIR / "source-env"


def add_env_val(
    env_key: str,
    env_val: str,
    description: str,
    auto_source: bool = False,
) -> None:
    _append_shell_text(f"# {description}\nexport {env_key}={env_val}")
    print_info(f"Adding {env_key} to source env")
    print_info(f"Description: {description}")
    if not auto_source:
        print_warning(
            "Run `source ~/.cliutils/source-env` to apply environment changes."
        )


def add_env_cmd(cmd: str, description: str) -> None:
    _append_shell_text(f"# {description}\n{cmd}")
    print_info(f"Adding {cmd} to source env")
    print_info(f"Description: {description}")
    print_warning(
        "Run `source ~/.cliutils/source-env` to apply environment changes."
    )


def clear_env() -> None:
    if SOURCE_ENV_PATH.exists():
        SOURCE_ENV_PATH.unlink()


def _append_shell_text(text: str) -> None:
    CLIUTILS_STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE_ENV_PATH.exists():
        SOURCE_ENV_PATH.write_text("#!/bin/sh\n", encoding="utf-8")
    SOURCE_ENV_PATH.chmod(0o600)
    with SOURCE_ENV_PATH.open("a", encoding="utf-8") as file:
        file.write(f"\n{text}\n")
