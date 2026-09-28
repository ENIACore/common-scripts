import getpass
from subprocess import CompletedProcess

# Colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
RESET = "\033[0m"
BOLD = "\033[1m"
GREY = "\033[90m"


def print_error(msg):
    print(f"  {BLUE}{BOLD}→{RESET}  {RED}{BOLD}[ERROR]{RESET}  {RED}{msg}{RESET}")


def print_success(msg):
    print(f"  {BLUE}{BOLD}→{RESET}  {GREEN}{BOLD}[SUCCESS]{RESET}  {GREEN}{msg}{RESET}")


def print_warning(msg):
    print(
        f"  {BLUE}{BOLD}→{RESET}  {YELLOW}{BOLD}[WARNING]{RESET}  {YELLOW}{msg}{RESET}"
    )


def print_info(msg):
    print(f"  {BLUE}{BOLD}→{RESET}  {BLUE}{BOLD}[INFO]{RESET}  {BLUE}{msg}{RESET}")


def print_step(msg):
    print(f"  {BLUE}{BOLD}→{RESET}  {CYAN}{BOLD}[STEP]{RESET}  {CYAN}{msg}{RESET}")


def print_header(msg):
    line = "=" * 60
    print(f"\n{MAGENTA}{BOLD}{line}{RESET}")
    print(f"{MAGENTA}{BOLD}{msg.center(60)}{RESET}")
    print(f"{MAGENTA}{BOLD}{line}{RESET}\n")


def print_group_start(title: str) -> None:
    print(f"  {BOLD}{BLUE}┌─ {title}{RESET}")
    print(f"  {BLUE}│{RESET}")


def print_group_step(msg: str = "") -> None:
    print(f"  {BLUE}│{RESET}  {msg}")


def print_group_end(msg: str = "", success: bool = True) -> None:
    color = GREEN if success else RED
    icon = "✓" if success else "✗"
    if msg:
        print(f"  {BLUE}│{RESET}")
        print(f"  {BLUE}└─{RESET} {color}{icon} {BOLD}{msg}{RESET}")
    else:
        print(f"  {BLUE}│{RESET}")
        print(f"  {BLUE}└─{RESET}")


def get_group_input(prompt, default: str = "") -> str:
    """Prompt user for input with optional default. Returns the input string."""
    if default:
        suffix = f" [{default}]: "
    else:
        suffix = ": "
    full_prompt = (
        f"  {BLUE}│{RESET}  {CYAN}{BOLD}[INPUT]{RESET} {CYAN}{prompt}{RESET}{suffix}"
    )
    reply: str = input(full_prompt).strip()
    return reply if reply else default


def get_group_password(prompt: str) -> str:
    """Prompt for a password in the group style without echoing its value."""
    full_prompt = (
        f"  {BLUE}│{RESET}  {CYAN}{BOLD}[INPUT]{RESET} "
        f"{CYAN}{prompt}{RESET}: "
    )
    return getpass.getpass(full_prompt)


def get_input(prompt, default: str = "") -> str:
    """Prompt user for input with optional default. Returns the input string."""
    if default:
        suffix = f" [{default}]: "
    else:
        suffix = ": "
    full_prompt = f"{CYAN}{BOLD}[INPUT]{RESET} {CYAN}{prompt}{RESET}{suffix}"
    reply: str = input(full_prompt).strip()
    return reply if reply else default


def run_cmd(cmd: str, capture_output: bool = False) -> CompletedProcess:
    """Run a shell command, printing it first. Raises on non-zero exit."""
    import subprocess

    print_step(f"Running: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=capture_output,
        text=True,
    )
    if result.returncode == 0:
        if capture_output and result.stdout:
            print_success(result.stdout.strip())
        else:
            print_success("Command completed successfully")
    else:
        err = result.stderr.strip() if capture_output and result.stderr else ""
        print_error(
            f"Command failed (exit {result.returncode}){': ' + err if err else ''}"
        )
        result.check_returncode()  # raises CalledProcessError
    return result
