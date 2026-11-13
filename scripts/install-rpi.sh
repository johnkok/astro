#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
ASTRO_USER=pi
SKIP_PINS=0
SKIP_CAN=0
SKIP_INDI_BUILD=0
FORCE_CONFIG=0
CAN_OSCILLATOR=12000000
CAN_INTERRUPT=25
BACKUP_ROOT=/var/backups/astro-stack

usage() {
    sed -n '1,80p' "$REPO_ROOT/docs/REPRODUCE.md"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --user) ASTRO_USER=$2; shift 2 ;;
        --skip-pins) SKIP_PINS=1; shift ;;
        --skip-can) SKIP_CAN=1; shift ;;
        --skip-indi-build) SKIP_INDI_BUILD=1; shift ;;
        --force-config) FORCE_CONFIG=1; shift ;;
        --can-oscillator) CAN_OSCILLATOR=$2; shift 2 ;;
        --can-interrupt) CAN_INTERRUPT=$2; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
    esac
done

if [[ ${EUID} -ne 0 ]]; then
    echo "Run as root: sudo $0" >&2
    exit 1
fi
if ! id "$ASTRO_USER" >/dev/null 2>&1; then
    echo "User does not exist: $ASTRO_USER" >&2
    exit 1
fi
if [[ ! $CAN_OSCILLATOR =~ ^[0-9]+$ || ! $CAN_INTERRUPT =~ ^[0-9]+$ ]]; then
    echo "CAN oscillator and interrupt must be integers" >&2
    exit 2
fi

ASTRO_HOME=$(getent passwd "$ASTRO_USER" | cut -d: -f6)
if [[ -z $ASTRO_HOME || ! -d $ASTRO_HOME ]]; then
    echo "Home directory is unavailable for $ASTRO_USER" >&2
    exit 1
fi

STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_ROOT"

backup_file() {
    local path=$1 rel
    [[ -e $path ]] || return 0
    rel=${path#/}
    rel=${rel//\//__}
    cp -a "$path" "$BACKUP_ROOT/${rel}.${STAMP}"
}

install_managed() {
    local mode=$1 source=$2 destination=$3
    backup_file "$destination"
    install -D -m "$mode" "$source" "$destination"
}

if [[ $(dpkg --print-architecture) != arm64 ]]; then
    echo "Warning: the reference stack is arm64; detected $(dpkg --print-architecture)" >&2
fi

if [[ $SKIP_PINS -eq 0 ]]; then
    install_managed 0644 "$REPO_ROOT/rpi/apt/pins-archive-keyring.gpg" \
        /usr/share/keyrings/pins-archive-keyring.gpg
    install_managed 0644 "$REPO_ROOT/rpi/apt/pins.list" \
        /etc/apt/sources.list.d/pins.list
fi

apt-get update
mapfile -t PACKAGES < <(grep -Ev '^[[:space:]]*(#|$)' \
    "$REPO_ROOT/rpi/apt/packages.txt")
if [[ $SKIP_PINS -eq 1 ]]; then
    FILTERED=()
    for package in "${PACKAGES[@]}"; do
        [[ $package == pins* || $package == phd2 ]] || FILTERED+=("$package")
    done
    PACKAGES=("${FILTERED[@]}")
fi
DEBIAN_FRONTEND=noninteractive apt-get install -y "${PACKAGES[@]}"

if [[ $SKIP_CAN -eq 0 ]]; then
    install_managed 0644 "$REPO_ROOT/rpi/network/80-can.network" \
        /etc/systemd/network/80-can.network
    systemctl enable systemd-networkd.service

    BOOT_CONFIG=/boot/firmware/config.txt
    if [[ ! -f $BOOT_CONFIG ]]; then
        echo "Boot configuration not found: $BOOT_CONFIG" >&2
        exit 1
    fi
    backup_file "$BOOT_CONFIG"
    CAN_LINES=(
        "dtparam=spi=on"
        "dtoverlay=mcp2515-can0,oscillator=$CAN_OSCILLATOR,interrupt=$CAN_INTERRUPT"
        "dtoverlay=spi0-hw-cs"
    )
    for line in "${CAN_LINES[@]}"; do
        grep -qxF "$line" "$BOOT_CONFIG" || printf '%s\n' "$line" >>"$BOOT_CONFIG"
    done
fi

DRIVER_ROOT=/opt/servo42d-ascom-alpaca
backup_file "$DRIVER_ROOT/config.json"
if [[ -e $DRIVER_ROOT/config.json && $FORCE_CONFIG -eq 0 ]]; then
    cp -a "$DRIVER_ROOT/config.json" "/tmp/astro-existing-config.$STAMP.json"
fi
mkdir -p "$DRIVER_ROOT"
cp -a "$REPO_ROOT/drivers/servo42d-alpaca/." "$DRIVER_ROOT/"
if [[ -e /tmp/astro-existing-config.$STAMP.json && $FORCE_CONFIG -eq 0 ]]; then
    cp -a "/tmp/astro-existing-config.$STAMP.json" "$DRIVER_ROOT/config.json"
    rm -f "/tmp/astro-existing-config.$STAMP.json"
fi
chown -R "$ASTRO_USER:$ASTRO_USER" "$DRIVER_ROOT"

if [[ ! -x $DRIVER_ROOT/.venv/bin/python ]]; then
    runuser -u "$ASTRO_USER" -- python3 -m venv "$DRIVER_ROOT/.venv"
fi
runuser -u "$ASTRO_USER" -- \
    "$DRIVER_ROOT/.venv/bin/pip" install --upgrade pip
runuser -u "$ASTRO_USER" -- \
    "$DRIVER_ROOT/.venv/bin/pip" install -e "$DRIVER_ROOT[test]"

if [[ $SKIP_INDI_BUILD -eq 0 ]]; then
    "$SCRIPT_DIR/build-indi-driver.sh"
fi

install -d -o "$ASTRO_USER" -g "$ASTRO_USER" \
    "$ASTRO_HOME/.indi" "$ASTRO_HOME/Documents/INDI"
install_managed 0644 "$REPO_ROOT/rpi/config/indi/Alpaca Telescope_config.xml" \
    "$ASTRO_HOME/.indi/Alpaca Telescope_config.xml"
install_managed 0644 "$REPO_ROOT/rpi/config/indi/Alpaca Telescope_config.xml" \
    "$ASTRO_HOME/.indi/Alpaca Telescope_config.xml.default"
install_managed 0644 "$REPO_ROOT/rpi/config/pins/3rdparty.json" \
    "$ASTRO_HOME/Documents/INDI/3rdparty.json"
chown "$ASTRO_USER:$ASTRO_USER" \
    "$ASTRO_HOME/.indi/Alpaca Telescope_config.xml" \
    "$ASTRO_HOME/.indi/Alpaca Telescope_config.xml.default" \
    "$ASTRO_HOME/Documents/INDI/3rdparty.json"

install_managed 0755 "$REPO_ROOT/rpi/bin/indi-alpaca-connect" \
    /usr/local/bin/indi-alpaca-connect

UNIT_TMP=$(mktemp -d)
trap 'rm -rf -- "$UNIT_TMP"' EXIT
for unit in pins.service servo42d-alpaca.service indi-alpaca-connect.service; do
    sed -e "s#User=pi#User=$ASTRO_USER#g" \
        -e "s#Group=pi#Group=$ASTRO_USER#g" \
        -e "s#/home/pi#$ASTRO_HOME#g" \
        "$REPO_ROOT/rpi/systemd/$unit" >"$UNIT_TMP/$unit"
    install_managed 0644 "$UNIT_TMP/$unit" "/etc/systemd/system/$unit"
done

systemctl daemon-reload
systemctl enable pins.service servo42d-alpaca.service indi-alpaca-connect.service
systemctl restart servo42d-alpaca.service
if [[ $SKIP_PINS -eq 0 ]]; then
    systemctl restart pins.service
    systemctl restart indi-alpaca-connect.service || true
fi

echo
echo "Installation complete. Reboot is required if CAN boot settings changed."
echo "Then run: $REPO_ROOT/scripts/verify-rpi.sh"

