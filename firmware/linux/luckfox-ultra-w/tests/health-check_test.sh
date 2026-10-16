#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HEALTH="$SCRIPT_DIR/../bin/health-check.sh"
PROBE="$SCRIPT_DIR/../bin/probe-rtsp.sh"
KNOWN_GOOD_CFG="$SCRIPT_DIR/../luckfox.cfg"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/sherman-luckfox-health.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT HUP INT TERM

make_fixture() {
    root=$1
    mkdir -p \
        "$root/etc" \
        "$root/dev" \
        "$root/proc/device-tree/syscon@ff000000/rgb" \
        "$root/proc/device-tree/panel" \
        "$root/proc/device-tree/spi@ff500000/spidev@0" \
        "$root/proc/device-tree/i2c@ff470000/sc3336@30" \
        "$root/proc/device-tree/csi2-dphy0" \
        "$root/proc/sys/kernel" \
        "$root/sys/kernel/config/device-tree/overlays/spi0m0" \
        "$root/sys/class/thermal/thermal_zone0" \
        "$root/run"

    printf 'Luckfox Pico Ultra W\000' >"$root/proc/device-tree/model"
    printf 'disabled\000' >"$root/proc/device-tree/syscon@ff000000/rgb/status"
    printf 'disabled\000' >"$root/proc/device-tree/panel/status"
    printf 'okay\000' >"$root/proc/device-tree/spi@ff500000/status"
    printf 'okay\000' >"$root/proc/device-tree/spi@ff500000/spidev@0/status"
    printf 'okay\000' >"$root/proc/device-tree/i2c@ff470000/sc3336@30/status"
    printf 'okay\000' >"$root/proc/device-tree/csi2-dphy0/status"
    cp "$KNOWN_GOOD_CFG" "$root/etc/luckfox.cfg"
    printf 'MemTotal:         185420 kB\n' >"$root/proc/meminfo"
    printf '5.10.160\n' >"$root/proc/sys/kernel/osrelease"
    printf '120.00 60.00\n' >"$root/proc/uptime"
    printf '59455\n' >"$root/sys/class/thermal/thermal_zone0/temp"
    : >"$root/dev/spidev0.0"
    : >"$root/dev/gpiochip1"
    : >"$root/dev/media0"
    : >"$root/dev/video0"
    : >"$root/run/rkipc.running"
    : >"$root/run/rtsp-554.listening"
    : >"$root/run/camera-streaming"
    : >"$root/run/sherman-face.running"
    printf '%s\n' '{"event":"face_runtime_health","state":"running","mode":"personality","personality_degraded":false}' \
        >"$root/run/sherman-face.health.json"
}

pass_fixture="$TMP_DIR/pass"
make_fixture "$pass_fixture"
pass_output=$($HEALTH --root "$pass_fixture" --format ndjson)
printf '%s\n' "$pass_output" | grep '"type":"summary","status":"PASS"' >/dev/null
printf '%s\n' "$pass_output" | grep '"name":"dt_sc3336"' >/dev/null
printf '%s\n' "$pass_output" | grep '"name":"rtsp_554"' >/dev/null
printf '%s\n' "$pass_output" | grep '"name":"personality_runtime","expected":"native","observed":"native"' >/dev/null

fail_fixture="$TMP_DIR/fail"
make_fixture "$fail_fixture"
sed -i.bak 's/^RGB_ENABLE=0$/RGB_ENABLE=1/' "$fail_fixture/etc/luckfox.cfg"
rm -f "$fail_fixture/etc/luckfox.cfg.bak" "$fail_fixture/dev/spidev0.0"
if $HEALTH --root "$fail_fixture" --format text >"$TMP_DIR/fail.out" 2>&1; then
    echo "expected unhealthy fixture to fail" >&2
    exit 1
fi
grep 'FAIL rgb_parallel' "$TMP_DIR/fail.out" >/dev/null
grep 'FAIL spi_device' "$TMP_DIR/fail.out" >/dev/null
grep 'summary status=FAIL' "$TMP_DIR/fail.out" >/dev/null

degraded_fixture="$TMP_DIR/degraded"
make_fixture "$degraded_fixture"
sed -i.bak 's/"personality_degraded":false/"personality_degraded":true/' \
    "$degraded_fixture/run/sherman-face.health.json"
rm -f "$degraded_fixture/run/sherman-face.health.json.bak"
degraded_output=$($HEALTH --root "$degraded_fixture" --format text)
printf '%s\n' "$degraded_output" | grep 'WARN personality_runtime' >/dev/null
printf '%s\n' "$degraded_output" | grep 'summary status=PASS' >/dev/null

if $HEALTH --format invalid >"$TMP_DIR/invalid.out" 2>&1; then
    echo "expected invalid output format to fail" >&2
    exit 1
fi

$PROBE --help >"$TMP_DIR/probe-help.out"
grep 'No frames are retained\|writes no camera frame' "$TMP_DIR/probe-help.out" >/dev/null
if $PROBE --timeout-seconds 0 robot-host >"$TMP_DIR/probe-invalid.out" 2>&1; then
    echo "expected zero RTSP timeout to fail" >&2
    exit 1
fi

echo "health-check tests: PASS"
