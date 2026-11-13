#!/usr/bin/env bash
set -Eeuo pipefail

DESTINATION=${1:-$PWD/artifacts}
STAMP=$(date +%Y%m%d-%H%M%S)
ARCHIVE="$DESTINATION/astro-rpi-backup-$STAMP.tar.gz"
mkdir -p "$DESTINATION"

PATHS=(
    opt/servo42d-ascom-alpaca/config.json
    etc/systemd/system/servo42d-alpaca.service
    etc/systemd/system/indi-alpaca-connect.service
    usr/local/bin/indi-alpaca-connect
    etc/systemd/network/80-can.network
    "home/pi/.indi/Alpaca Telescope_config.xml"
    home/pi/Documents/INDI/3rdparty.json
    home/pi/.PHDGuidingV2
    home/pi/SERVO42D_CHANGE_HISTORY.md
)

EXISTING=()
for path in "${PATHS[@]}"; do
    [[ -e /$path ]] && EXISTING+=("$path")
done
tar -C / -czf "$ARCHIVE" "${EXISTING[@]}"
chmod 0600 "$ARCHIVE"
echo "$ARCHIVE"
echo "Private backup: it may contain camera identifiers and site settings."

