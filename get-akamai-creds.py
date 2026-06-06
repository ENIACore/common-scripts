#!/usr/bin/env python3

import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "bin" / "_lib"))
from formatting import (
    GREEN,
    RED,
    RESET,
    print_group_end,
    print_group_start,
    print_group_step,
)

creds_raw = Path("~/.akamai-creds").expanduser().read_text().strip()
creds = base64.b64decode(creds_raw).decode()
username, password = creds.split(":", 1)
username = username.strip()
password = password.strip()

print()
print_group_start("Akamai Credentials")
print_group_step(f"Username: {GREEN}{username}{RESET}")
print_group_step(f"Password: {RED}{password}{RESET}")
print_group_end()
