#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo "Run as root: sudo $0" >&2
    exit 1
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
INDI_TAG=${INDI_TAG:-v2.2.5}
SOURCE_DIR=${INDI_SOURCE_DIR:-/usr/local/src/indi-astro-v2.2.5}
BUILD_DIR=${INDI_BUILD_DIR:-$SOURCE_DIR/build-astro}
JOBS=${JOBS:-$(nproc)}
BACKUP_ROOT=${BACKUP_ROOT:-/var/backups/astro-stack}
STAMP=$(date +%Y%m%d-%H%M%S)

mkdir -p "$(dirname -- "$SOURCE_DIR")" "$BACKUP_ROOT"

if [[ ! -d $SOURCE_DIR/.git ]]; then
    git clone --depth 1 --branch "$INDI_TAG" \
        https://github.com/indilib/indi.git "$SOURCE_DIR"
else
    git -C "$SOURCE_DIR" fetch --depth 1 origin "refs/tags/$INDI_TAG:refs/tags/$INDI_TAG"
    git -C "$SOURCE_DIR" checkout --detach "$INDI_TAG"
fi

install -m 0644 \
    "$REPO_ROOT/drivers/indi-alpaca-telescope/indi_alpaca_telescope.cpp" \
    "$SOURCE_DIR/drivers/telescope/indi_alpaca_telescope.cpp"
install -m 0644 \
    "$REPO_ROOT/drivers/indi-alpaca-telescope/indi_alpaca_telescope.h" \
    "$SOURCE_DIR/drivers/telescope/indi_alpaca_telescope.h"

cmake -S "$SOURCE_DIR" -B "$BUILD_DIR" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DINDI_BUILD_QT_CLIENT=OFF \
    -DINDI_BUILD_UNITTESTS=OFF \
    -DINDI_BUILD_INTEGTESTS=OFF
cmake --build "$BUILD_DIR" --target indi_alpaca_telescope --parallel "$JOBS"

BUILT_BINARY="$BUILD_DIR/drivers/telescope/indi_alpaca_telescope"
if [[ ! -x $BUILT_BINARY ]]; then
    echo "Expected build output not found: $BUILT_BINARY" >&2
    exit 1
fi

if [[ -e /usr/bin/indi_alpaca_telescope ]]; then
    cp -a /usr/bin/indi_alpaca_telescope \
        "$BACKUP_ROOT/indi_alpaca_telescope.$STAMP"
fi
install -m 0755 "$BUILT_BINARY" /usr/bin/indi_alpaca_telescope

/usr/bin/indi_alpaca_telescope --help >/dev/null 2>&1 || true
echo "Installed customized INDI Alpaca telescope driver from $INDI_TAG"

