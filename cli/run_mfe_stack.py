#!/usr/bin/env python3

import subprocess
import sys
import time
import urllib.error
import urllib.request

from cliutils.formatting import (
    BOLD,
    CYAN,
    GREEN,
    GREY,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    get_group_input,
    print_group_end,
    print_group_start,
    print_group_step,
    print_header,
    print_warning,
)
from cliutils.tmux import run_tmux

SESSION = "local-mfe"

BRANDS = ["pb", "ws", "wse", "pt", "pk", "wsk", "mk", "land", "rh", "rh-modern"]

WINDOWS: list[tuple[str, str, int]] = [
    ("server", "docker system prune -f && run-server", 0),
    ("adg", "run-adg", 10),
    (
        "brand-configs",
        "export REQUIRED_NODE_VERSION=22 && build-brand-configs USA {brand}",
        15,
    ),
    ("global", "run-global", 8),
    ("content", "run-content", 8),
    ("shop", "run-shop", 8),
    ("product", "run-product", 8),
    ("phygital", "run-phygital", 8),
    ("customer", "run-customer", 8),
    ("registry", "run-registry", 8),
    ("order-srv", "run-order-servicing", 8),
]

HEARTBEAT_URLS = ["http://localhost:9090/heartbeat", "http://localhost:9091/heartbeat"]
HEARTBEAT_TIMEOUT = 300
HEARTBEAT_INTERVAL = 5


def session_exists() -> bool:
    return run_tmux(["has-session", "-t", SESSION], check=False).returncode == 0


def new_window(name: str, cmd: str) -> None:
    run_tmux(["new-window", "-t", SESSION, "-n", name])
    run_tmux(["send-keys", "-t", f"{SESSION}:{name}", cmd, "Enter"])


def wait_with_progress(seconds: int, label: str) -> None:
    for i in range(seconds, 0, -1):
        print(
            f"\r  {CYAN}│{RESET}  {GREY}Waiting {i:2d}s for {label} to initialise…{RESET}",
            end="",
            flush=True,
        )
        time.sleep(1)
    print(f"\r  {CYAN}│{RESET}  {GREEN}✓ Done waiting for {label:<30}{RESET}")


def _heartbeat_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            return 200 <= resp.status < 300
    except (TimeoutError, urllib.error.URLError):
        return False


def wait_for_server() -> None:
    print_group_start("Waiting for server heartbeats")
    for url in HEARTBEAT_URLS:
        print_group_step(f"{GREY}  {url}{RESET}")
    print_group_step()

    elapsed = 0
    while elapsed < HEARTBEAT_TIMEOUT:
        results = {url: _heartbeat_ok(url) for url in HEARTBEAT_URLS}
        status_parts = [
            f"{GREEN}✓{RESET} {GREY}{url}{RESET}"
            if ok
            else f"{RED}✗{RESET} {GREY}{url}{RESET}"
            for url, ok in results.items()
        ]
        print(
            f"\r  {CYAN}│{RESET}  {'  '.join(status_parts)}  {GREY}({HEARTBEAT_TIMEOUT - elapsed}s remaining){RESET}   ",
            end="",
            flush=True,
        )
        if all(results.values()):
            print()
            print_group_end(
                "Server is healthy — both heartbeats responded", success=True
            )
            print()
            return
        time.sleep(HEARTBEAT_INTERVAL)
        elapsed += HEARTBEAT_INTERVAL

    print()
    print_group_end(
        f"Server did not become healthy within {HEARTBEAT_TIMEOUT}s — check the server window",
        success=False,
    )
    print_warning(
        "Continuing anyway; brand-configs may fail if containers aren't ready."
    )
    print()


def preflight_check() -> bool:
    print_header("local-mfe  |  tmux session launcher")
    print_group_start(f"{YELLOW}{BOLD}Pre-flight checklist{RESET}")
    checks = [
        "All dev scripts installed",
        "Global npm packages installed",
        "All repos installed via install-core-repos",
        "All brew packages installed via install-brew-packages",
        "All ports/configurations changed in accordance with dev setup",
        "All endpoints set via set-endpoints",
        "All samples copied via copy-sample-to-actual",
        "Etcd configured via config-build-etcd",
        "All mfes installed via build-mfes",
        "Ecom-app-checkout installed via npm i and npm run build-config-service-ci",
        "ADG config service built via build-adg-config-service",
        "Oracle auth set via set-oracle-auth",
        "Generations added via build-schedules",
        "Any other setup steps from mfe-setup.md",
        "No stale tmux session named 'local-mfe' already running",
    ]
    for c in checks:
        print_group_step(f"{YELLOW}⚠  {c}{RESET}")
    print_group_step()
    print_warning("This script only handles the RUN phase, not the build phase.")
    print_group_step()
    answer = get_group_input(
        f"Have you completed all build/config steps above? {GREY}(y/N){RESET}",
        default="N",
    )
    if answer.lower() != "y":
        print_group_end("Aborted — complete the build steps first.", success=False)
        return False
    print_group_end("Pre-flight confirmed", success=True)
    print()
    return True


def pick_brand() -> str:
    print_group_start("Brand selection")
    for i, b in enumerate(BRANDS, 1):
        print_group_step(f"  {GREY}{i}.{RESET}  {BOLD}{CYAN}{b}{RESET}")
    print_group_step()
    choice = get_group_input(f"Enter brand number or name  {GREY}(e.g. 1 or pb){RESET}")

    if choice.isdigit() and 1 <= int(choice) <= len(BRANDS):
        brand = BRANDS[int(choice) - 1]
        print_group_end(f"Brand: {CYAN}{brand}{RESET}", success=True)
        return brand

    if choice.lower() in BRANDS:
        print_group_end(f"Brand: {CYAN}{choice.lower()}{RESET}", success=True)
        return choice.lower()

    print_group_end(f"Unknown brand '{choice}' — defaulting to pb", success=False)
    return "pb"


def ensure_etcd() -> None:
    print_group_start("etcd health check")
    result = subprocess.run(
        ["brew", "services", "list"], capture_output=True, text=True, check=True
    )
    etcd_running = any(
        "etcd" in line and "started" in line for line in result.stdout.splitlines()
    )
    if etcd_running:
        print_group_step(f"{GREEN}etcd is already running{RESET}")
        print_group_end("etcd OK", success=True)
    else:
        print_group_step(f"{YELLOW}etcd not running — calling start-etcd…{RESET}")
        r = subprocess.run(["start-etcd"], capture_output=True, text=True)
        if r.returncode == 0:
            print_group_end("etcd started via start-etcd", success=True)
        else:
            print_group_end(
                f"start-etcd failed (exit {r.returncode}) — check manually",
                success=False,
            )
            print_warning("Continuing anyway; some services may fail to connect.")
    print()


def kill_existing_session() -> int | None:
    if not session_exists():
        return None
    print_group_start(f"Existing session '{SESSION}' detected")
    answer = get_group_input(
        f"{YELLOW}Kill it and start fresh?{RESET}  {GREY}(y/N){RESET}",
        default="N",
    )
    if answer.lower() == "y":
        run_tmux(["kill-session", "-t", SESSION])
        print_group_end("Old session killed", success=True)
    else:
        print_group_end("Keeping existing session — attaching instead.", success=False)
        result = run_tmux(
            ["attach-session", "-t", SESSION],
            check=False,
            capture_output=False,
        )
        return result.returncode
    print()
    return None


def create_session() -> None:
    print_group_start(f"Creating tmux session  '{SESSION}'")
    run_tmux(["new-session", "-d", "-s", SESSION, "-n", "server"])
    print_group_end(f"Session '{SESSION}' created", success=True)
    print()


def launch_windows(brand: str) -> None:
    print_group_start("Launching service windows")
    first = True
    for name, cmd_template, delay in WINDOWS:
        cmd = cmd_template.format(brand=brand)
        if first:
            run_tmux(["send-keys", "-t", f"{SESSION}:server", cmd, "Enter"])
            first = False
        else:
            new_window(name, cmd)
        print_group_step(
            f"{GREEN}✓{RESET}  {BOLD}{CYAN}{name:<18}{RESET}  {GREY}{cmd}{RESET}"
        )
        if name == "server":
            print_group_end("All windows registered", success=True)
            print()
            wait_for_server()
            print_group_start("Continuing window launches")
        elif delay > 0:
            wait_with_progress(delay, name)
    print_group_end("All windows launched", success=True)
    print()


def attach() -> int:
    print_group_start("Attaching to session")
    print_group_step(
        f"Use  {CYAN}Ctrl-b w{RESET}  to browse windows, "
        f"{CYAN}Ctrl-b [{RESET}  to scroll output."
    )
    print_group_end(f"Attaching to  {MAGENTA}{SESSION}{RESET}")
    print()
    result = run_tmux(
        ["attach-session", "-t", SESSION], check=False, capture_output=False
    )
    return result.returncode


def main() -> int:
    try:
        if not preflight_check():
            return 0
        brand = pick_brand()
        print()
        ensure_etcd()
        existing_session_status = kill_existing_session()
        if existing_session_status is not None:
            return existing_session_status
        create_session()
        launch_windows(brand)
        return attach()
    except (OSError, subprocess.CalledProcessError) as error:
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            detail = error.stderr.strip()
        else:
            detail = str(error)
        print_group_start("Launcher error")
        print_group_end(detail, success=False)
        return 1


if __name__ == "__main__":
    sys.exit(main())
