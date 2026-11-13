#!/usr/bin/env python3
"""Patch only the INDI/Alpaca mount fields in an existing N.I.N.A. profile."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import stat
import tempfile
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    profile = args.profile.expanduser().resolve()
    if not profile.is_file():
        parser.error(f"profile does not exist: {profile}")

    settings_path = (
        Path(__file__).resolve().parent.parent
        / "rpi/config/nina/mount-settings.json"
    )
    settings = json.loads(settings_path.read_text(encoding="utf-8"))

    # Validate the profile as XML, but patch its raw text so ElementTree does not
    # rewrite N.I.N.A.'s many locally reused namespace prefixes.
    ET.parse(profile)
    original = profile.read_text(encoding="utf-8")
    block_match = re.search(
        r"<TelescopeSettings(?:\s[^>]*)?>.*?</TelescopeSettings>",
        original,
        flags=re.DOTALL,
    )
    if block_match is None:
        raise SystemExit("TelescopeSettings was not found in the profile")
    block = block_match.group(0)
    changes: list[tuple[str, str | None, str]] = []
    for key, value in settings.items():
        field_pattern = re.compile(
            rf"(<{re.escape(key)}(?:\s[^>]*)?>)(.*?)(</{re.escape(key)}>)",
            flags=re.DOTALL,
        )
        field_match = field_pattern.search(block)
        if field_match is None:
            raise SystemExit(f"profile is missing field: {key}")
        old = html.unescape(field_match.group(2))
        if old != value:
            changes.append((key, old, value))
            replacement = rf"\g<1>{html.escape(value)}\g<3>"
            block = field_pattern.sub(replacement, block, count=1)

    if not changes:
        print("N.I.N.A. mount settings already match")
        return 0

    for key, old, new in changes:
        print(f"{key}: {old!r} -> {new!r}")
    if args.dry_run:
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = profile.with_name(f"{profile.name}.bak-{stamp}")
    shutil.copy2(profile, backup)

    updated = original[: block_match.start()] + block + original[block_match.end() :]
    original_mode = stat.S_IMODE(profile.stat().st_mode)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{profile.name}.", dir=profile.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(updated, encoding="utf-8")
        os.chmod(temporary, original_mode)
        os.replace(temporary, profile)
    finally:
        temporary.unlink(missing_ok=True)

    print(f"Updated {profile}")
    print(f"Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

