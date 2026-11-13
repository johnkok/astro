#!/usr/bin/env bash
set -Eeuo pipefail

REMOTE=${1:-pi@192.168.1.44}
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)

if ! git -C "$REPO_ROOT" diff --quiet || \
   ! git -C "$REPO_ROOT" diff --cached --quiet; then
    echo "Refusing to overwrite a dirty repository. Commit or stash changes first." >&2
    exit 1
fi

scp -F /dev/null "$REMOTE:/opt/servo42d-ascom-alpaca/src/servo42d_ascom/*.py" \
    "$REPO_ROOT/drivers/servo42d-alpaca/src/servo42d_ascom/"
scp -F /dev/null \
    "$REMOTE:/opt/servo42d-ascom-alpaca/pyproject.toml" \
    "$REMOTE:/opt/servo42d-ascom-alpaca/README.md" \
    "$REMOTE:/opt/servo42d-ascom-alpaca/config.example.json" \
    "$REMOTE:/opt/servo42d-ascom-alpaca/config.json" \
    "$REPO_ROOT/drivers/servo42d-alpaca/"
scp -F /dev/null \
    "$REMOTE:/home/pi/Projects/indi-v225-guide-fix/drivers/telescope/indi_alpaca_telescope.cpp" \
    "$REMOTE:/home/pi/Projects/indi-v225-guide-fix/drivers/telescope/indi_alpaca_telescope.h" \
    "$REPO_ROOT/drivers/indi-alpaca-telescope/"
scp -F /dev/null \
    "$REMOTE:/etc/systemd/system/servo42d-alpaca.service" \
    "$REMOTE:/etc/systemd/system/indi-alpaca-connect.service" \
    "$REMOTE:/etc/systemd/system/pins.service" \
    "$REPO_ROOT/rpi/systemd/"
scp -F /dev/null "$REMOTE:/usr/local/bin/indi-alpaca-connect" \
    "$REPO_ROOT/rpi/bin/"
scp -F /dev/null "$REMOTE:/home/pi/SERVO42D_CHANGE_HISTORY.md" \
    "$REPO_ROOT/docs/PI_CHANGE_HISTORY.md"

echo "Export complete. Full N.I.N.A./PHD2 profiles and tests were not exported."
echo "Review git diff and manually import reviewed test changes if required."

