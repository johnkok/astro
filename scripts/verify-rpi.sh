#!/usr/bin/env bash
set -uo pipefail

FAILURES=0
pass() { printf 'PASS  %s\n' "$*"; }
fail() { printf 'FAIL  %s\n' "$*" >&2; FAILURES=$((FAILURES + 1)); }

check_service() {
    local unit=$1
    if systemctl is-active --quiet "$unit"; then
        pass "$unit is active"
    else
        fail "$unit is not active"
    fi
}

check_service pins.service
check_service servo42d-alpaca.service
if systemctl is-active --quiet indi-alpaca-connect.service; then
    pass "indi-alpaca-connect.service completed"
else
    fail "indi-alpaca-connect.service did not complete"
fi

if ip -details link show can0 2>/dev/null | grep -q 'bitrate 500000'; then
    pass "can0 is configured for 500 kbit/s"
else
    fail "can0 is absent or has the wrong bitrate"
fi

if curl -fsS --max-time 3 \
    'http://127.0.0.1:11111/management/v1/configureddevices' \
    | grep -q 'Servo42D Equatorial Mount'; then
    pass "Servo42D Alpaca management endpoint responds"
else
    fail "Servo42D Alpaca endpoint did not respond"
fi

if curl -fsS --max-time 3 \
    'http://127.0.0.1:11111/api/v1/telescope/0/name?ClientID=9001&ClientTransactionID=1' \
    | grep -q 'Servo42D Equatorial Mount'; then
    pass "Alpaca telescope device 0 responds"
else
    fail "Alpaca telescope device 0 did not respond"
fi

if command -v indi_getprop >/dev/null 2>&1 && \
   indi_getprop -h 127.0.0.1 -p 7624 \
       'Alpaca Telescope.CONNECTION.CONNECT' 2>/dev/null | grep -q '=On$'; then
    pass "INDI Alpaca Telescope is connected"
else
    fail "INDI Alpaca Telescope is not connected"
fi

if [[ $FAILURES -eq 0 ]]; then
    echo "All checks passed."
    exit 0
fi
echo "$FAILURES check(s) failed." >&2
exit 1

