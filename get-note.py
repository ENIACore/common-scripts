#!/usr/bin/env python3

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "bin" / "_lib"))
from common import copy_to_clipboard
from formatting import (
    BOLD,
    CYAN,
    GREEN,
    GREY,
    MAGENTA,
    RED,
    RESET,
    WHITE,
    YELLOW,
    get_group_input,
    print_group_end,
    print_group_start,
    print_group_step,
)

# ── Highlight colors ──────────────────────────────────────────────────────────
COMMAND_COLOR = CYAN  # shell commands / executables
FLAG_COLOR = YELLOW  # --flags and -f
PATH_COLOR = GREEN  # /absolute/paths or ~/tilde/paths
PLACEHOLDER_COLOR = RED  # <placeholder> tokens
COMMENT_COLOR = WHITE  # # comments

_TOKEN_RE = re.compile(
    r"(?P<comment>#[^\n]*)"
    r"|(?P<placeholder><[^>]+>)"
    r"|(?P<path>(?:~/|/)\S+)"
    r"|(?P<flag>(?<!\w)--?\w[\w-]*)"
    r"|(?P<command>(?:^|\|\s*)(\w[\w.-]*))",
    re.MULTILINE,
)
_COLOR_BY_GROUP = {
    "comment": COMMENT_COLOR,
    "placeholder": PLACEHOLDER_COLOR,
    "path": PATH_COLOR,
    "flag": FLAG_COLOR,
    "command": COMMAND_COLOR,
}


# ── Note entries ──────────────────────────────────────────────────────────────
# Add your notes here.  Each entry has:
#   description : one-line summary shown in the list
#   type        : "command" | "template" | "directory" | "snippet" | "note"
#   text        : list of strings (one per line)
# ─────────────────────────────────────────────────────────────────────────────
NOTES: dict[str, dict] = {
    "SITES-INSTALL-COMPONENTS": {
        "description": "Install built web components into sites from svn/trunk/sites/common/content/build-tools; used to deploy changes to qa665",
        "type": "template",
        "text": [
            "npm install --save --save-exact --package-lock-only @web-component-ecom-checkout/checkout-application@<published-web-comp-build> && npm install --save --save-exact --package-lock-only  @web-component-ecom-checkout/checkout-experimentation@<published-web-comp-build> && npm install --save --save-exact --package-lock-only  @web-component-ecom-checkout/checkout-foundation@<published-web-comp-build> && npm install --save --save-exact --package-lock-only  @web-component-ecom-checkout/checkout-observable@<published-web-comp-build> && npm install --save --save-exact --package-lock-only  @web-component-ecom-checkout/checkout-sites@<published-web-comp-build>",
        ],
    },
    "CHECKOUT-SVN-SHORTCUT": {
        "description": "Checkout svn shortcut - replace trunk with 26.xx-shortcut (run this from ~/work/svn directory)",
        "type": "template",
        "text": [
            "svn checkout https://<svn-host>/svn/shortcuts/evolution/trunk trunk",
        ],
    },
    "DOCKER-CLEAN": {
        "description": "Remove all stopped containers, dangling images, unused volumes",
        "type": "command",
        "text": [
            "docker system prune -af --volumes",
        ],
    },
    "GET-CART-ITEMS": {
        "description": "Get cart items json (which is originally received via fetchCart call to /shopping-cart/index.json",
        "type": "text",
        "text": [
            "console.log(JSON.stringify({ shoppingCart: window.__VUE_APP.config.globalProperties.$store.state.checkout.cartData }, null, 2))"
        ],
    },
    "DP-BUILD-FLOW": {
        "description": "Flow for building the dp sites",
        "type": "text",
        "text": [
            "1. Push changes to svc (i.e ecom-svc-checkout) and get the published name",
            "2. Add the published name to that services version in dp-baselogic's master pom.xml",
            "3. Commit changes and wait for dp-baselogic build to succeed",
            "4. Trigger dp-baselogic build at https://<jenkins-host>/job/<project>/job/dp-sites/job/<brand>/",
            "5. Pull in build to QA via https://<jenkins-host>/view/deploy-<env>-<project>/ WAR button",
        ],
    },
    "SETUP-DOCKER-ENVIRONMENT": {
        "description": "Sets (or resets) docker environment for integration tests. If encountering integration issues run this first",
        "type": "text",
        "text": [
            "$(export DOCKER_HOST=unix:///var/run/docker.sock) && $(sudo ln -sf /Users/clamkin/.rd/docker.sock /var/run/docker.sock)"
        ],
    },
    "PRUNE-MVN-BUILD-ARTIFACTS": {
        "description": "Dry prune all maven build artifacts, used for corrupted builds",
        "type": "text",
        "text": [
            "find . -type d -name target -prune -exec rm -rf {} +",
        ],
    },
    "SETUP-MVN-CLEAN-INSTALL": {
        "description": "Removes all build artifacts, caches, and potential issues before mvn clean install",
        "type": "text",
        "text": [
            "$(export DOCKER_HOST=unix:///var/run/docker.sock) && $(sudo ln -sf /Users/clamkin/.rd/docker.sock /var/run/docker.sock) $(rm -f ~/.testcontainers.properties) && $(find . -type d -name target -prune -exec rm -rf {} +)",
        ],
    },
    "RUN-LOCAL-TESTS": {
        "description": "Run all local tests",
        "type": "text",
        "text": [
            "mvn verify -Dstubrunner.username=<username> -Dstubrunner.password=This-Is-A-Day",
        ],
    },
    "LOCAL-CLEAN-INSTALL": {
        "description": "Run clean install",
        "type": "text",
        "text": [
            "mvn clean install -U -Dstubrunner.username=<username> -Dstubrunner.password=This-Is-A-Day",
        ],
    },
    "MODULE-COMPILE-RETEST": {
        "description": "Install specific module and retest specific files (values in <> are examples to be replaced). Use -am if you prefer to also make the modules relied on (often times not needed).",
        "type": "text",
        "text": [
            "mvn install -Dstubrunner.username=<username> -Dstubrunner.password=This-Is-A-Day -Dmaven.javadoc.skip=true -DfailIfNoTests=false -pl <activities/cart> -Dtest=<CheckoutResponseMapperTest,SavedCreditCardHelperTest>",
        ],
    },
    "FAST-LOCAL-CLEAN-INSTALL": {
        "description": "Run clean install fast",
        "type": "text",
        "text": [
            "mvn clean install -U -Dstubrunner.username=<username> -Dstubrunner.password=This-Is-A-Day -DskipTests -Dmaven.javadoc.skip=true",
        ],
    },
    "ADG-LOCAL-CLEAN-INSTALL": {
        "description": "Run clean install fast on ADG (requires specific flag)",
        "type": "text",
        "text": [
            "mvn clean install -U -Dstubrunner.username=<username> -Dstubrunner.password=This-Is-A-Day -DprotocArtifact=com.google.protobuf:protoc:3.11.1:exe:osx-x86_64 -DskipITs=true",
        ],
    },
    "ADG-FAST-LOCAL-CLEAN-INSTALL": {
        "description": "Run clean install fast on ADG (requires specific flag)",
        "type": "text",
        "text": [
            "mvn clean install -U -Dstubrunner.username=<username> -Dstubrunner.password=This-Is-A-Day -DskipTests -Dmaven.javadoc.skip=true -Dos.arch=x86_64",
        ],
    },
    "JENKINS-LOGVIEW-CREDS": {
        "description": "Credentials to view logs of jenkins builds (find link in console output)",
        "type": "text",
        "text": [
            "Username: *****",
            "Password: *****",
        ],
    },
}

NOTE_NAMES = list(NOTES.keys())

# ── Type badge colors ─────────────────────────────────────────────────────────
_TYPE_COLORS: dict[str, str] = {
    "command": CYAN,
    "template": YELLOW,
    "directory": GREEN,
    "snippet": MAGENTA,
    "note": WHITE,
}


def _type_badge(type_str: str) -> str:
    color = _TYPE_COLORS.get(type_str.lower(), WHITE)
    return f"{color}[{type_str}]{RESET}"


# ── Syntax highlighting ───────────────────────────────────────────────────────
def highlight_line(line: str) -> str:
    def colorize(match: re.Match) -> str:
        kind = match.lastgroup
        if kind not in _COLOR_BY_GROUP:
            return match.group()
        return f"{_COLOR_BY_GROUP[kind]}{match.group()}{RESET}"

    return _TOKEN_RE.sub(colorize, line)


# ── Print a single note ───────────────────────────────────────────────────────
def print_note(name: str, entry: dict) -> None:
    badge = _type_badge(entry["type"])
    print()
    print_group_start(
        f"NOTE: {YELLOW}{name}{RESET}  {badge}  {GREY}{entry['description']}{RESET}"
    )
    for line in entry["text"]:
        print_group_step(highlight_line(line))

    text_str = "\n".join(entry["text"])
    tool = copy_to_clipboard(text_str)
    if tool:
        print_group_end(f"Copied to clipboard {GREY}(via {tool}){RESET}")
    else:
        print_group_end(
            "Could not copy — install pbcopy / xclip / xsel / wl-copy",
            success=False,
        )


# ── Interactive list ──────────────────────────────────────────────────────────
def print_list(filter_type: str = "") -> int:
    names = [
        n
        for n in NOTE_NAMES
        if not filter_type or NOTES[n]["type"].lower() == filter_type.lower()
    ]
    if not names:
        print()
        print_group_start("No notes found")
        print_group_end(f"No notes of type '{filter_type}'", success=False)
        return -1

    print()
    print_group_start(
        "Available notes"
        + (f"  {GREY}(filter: {filter_type}){RESET}" if filter_type else "")
    )
    for i, name in enumerate(names, 1):
        entry = NOTES[name]
        badge = _type_badge(entry["type"])
        print_group_step(
            f"{GREY}{i}.{RESET} {BOLD}{YELLOW}{name}{RESET}  {badge}  {GREY}{entry['description']}{RESET}"
        )

    print_group_step()
    choice: str = get_group_input(f"Enter a number to copy, or {GREY}q{RESET} to quit")
    if choice.lower() == "q" or choice == "":
        print_group_end()
        return -1
    if choice.isdigit() and 1 <= int(choice) <= len(names):
        print_group_end()
        # map filtered index back to original name
        _chosen_name = names[int(choice) - 1]
        return NOTE_NAMES.index(_chosen_name)
    else:
        print_group_end(f"Invalid choice: {choice}", False)
        return -1


# ── Entry point ───────────────────────────────────────────────────────────────
def usage() -> None:
    print(f"\n  {BOLD}Usage:{RESET}")
    print(f"    get-note                    {GREY}# interactive list{RESET}")
    print(
        f"    get-note ls [type]          {GREY}# list (optionally filter by type){RESET}"
    )
    print(f"    get-note <KEY>              {GREY}# copy note directly{RESET}")
    print(f"\n  {BOLD}Types:{RESET}  command  template  directory  snippet  note\n")


def main(argv: list[str]) -> int:
    arg = argv[1].strip() if len(argv) > 1 else ""
    filter_arg = argv[2].strip() if len(argv) > 2 else ""

    # ── list mode ─────────────────────────────────────────────────────────────
    if arg in ("ls", "list", ""):
        choice = print_list(filter_arg)
        if choice == -1:
            return 1
        name = NOTE_NAMES[choice]
        entry = NOTES[name]
        print_note(name, entry)
        return 0

    # ── help ──────────────────────────────────────────────────────────────────
    if arg in ("-h", "--help", "help"):
        usage()
        return 0

    # ── direct lookup ─────────────────────────────────────────────────────────
    entry = NOTES.get(arg.upper())
    if entry is None:
        print()
        print_group_start("Error")
        print_group_step(f"{RED}Unknown note:{RESET} {BOLD}{arg}{RESET}")
        print_group_end(
            f"Run {BOLD}get-note ls{RESET} to see available notes.", success=False
        )
        return 1

    print_note(arg.upper(), entry)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
