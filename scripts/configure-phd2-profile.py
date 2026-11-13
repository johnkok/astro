#!/usr/bin/env python3
"""Patch mount fields in one PHD2 profile without changing camera settings."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import tempfile
from datetime import datetime
from pathlib import Path


VALUES = {
    "scope": {"LastMenuChoice": "INDI Mount [Alpaca Telescope]"},
    "AlpacaMount": {"Endpoint": "127.0.0.1:11111:0"},
    "indi": {"INDImount": "Alpaca Telescope"},
}


def replace_section(lines: list[str], section: str, values: dict[str, str]) -> list[str]:
    header = f"[{section}]"
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip("\r\n") == header)
    except StopIteration:
        if lines and lines[-1].strip():
            lines.append("\n")
        lines.append(header + "\n")
        lines.extend(f"{key}={value}\n" for key, value in values.items())
        return lines

    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("[")),
        len(lines),
    )
    found: set[str] = set()
    for index in range(start + 1, end):
        key = lines[index].split("=", 1)[0] if "=" in lines[index] else ""
        if key in values:
            lines[index] = f"{key}={values[key]}\n"
            found.add(key)
    for key, value in values.items():
        if key not in found:
            lines.insert(end, f"{key}={value}\n")
            end += 1
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--profile", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = args.config.expanduser().resolve()
    if not config.is_file():
        parser.error(f"configuration does not exist: {config}")

    original = config.read_text(encoding="utf-8").splitlines(keepends=True)
    updated = list(original)
    for suffix, values in VALUES.items():
        updated = replace_section(updated, f"profile/{args.profile}/{suffix}", values)

    if updated == original:
        print("PHD2 mount settings already match")
        return 0
    if args.dry_run:
        print("PHD2 mount settings need updating")
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = config.with_name(f"{config.name}.bak-{stamp}")
    shutil.copy2(config, backup)

    original_mode = stat.S_IMODE(config.stat().st_mode)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{config.name}.", dir=config.parent)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
        stream.writelines(updated)
    temporary = Path(temporary_name)
    os.chmod(temporary, original_mode)
    os.replace(temporary, config)
    print(f"Updated {config}")
    print(f"Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

