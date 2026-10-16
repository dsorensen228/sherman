#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
INIT_SCRIPT=$SCRIPT_DIR/../init/S99sherman-face
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/sherman-face-service.XXXXXX")

cleanup() {
    if [ -r "$TMP_DIR/run/face.pid" ]; then
        fixture_pid=$(sed -n '1p' "$TMP_DIR/run/face.pid")
        case "$fixture_pid" in
            ''|*[!0-9]*) ;;
            *) kill -KILL "$fixture_pid" 2>/dev/null || true ;;
        esac
    fi
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT HUP INT TERM

mkdir -p "$TMP_DIR/bin" "$TMP_DIR/proc" "$TMP_DIR/run" "$TMP_DIR/app"
: >"$TMP_DIR/app/run_face.py"
: >"$TMP_DIR/app/eyes.so"
: >"$TMP_DIR/app/personality.so"
: >"$TMP_DIR/app/config.json"

PATH=$SCRIPT_DIR/fixtures:$PATH
export PATH
export SHERMAN_FACE_DAEMON=/bin/sh
export SHERMAN_FACE_APP=$TMP_DIR/app/run_face.py
export SHERMAN_FACE_PID_FILE=$TMP_DIR/run/face.pid
export SHERMAN_EYES_LIBRARY=$TMP_DIR/app/eyes.so
export SHERMAN_PERSONALITY_LIBRARY=$TMP_DIR/app/personality.so
export SHERMAN_FACE_CONFIG=$TMP_DIR/app/config.json
export SHERMAN_FACE_PYTHONPATH=$TMP_DIR/app
export SHERMAN_FACE_HEALTH_FILE=$TMP_DIR/run/health.json
export SHERMAN_FACE_ERROR_FILE=$TMP_DIR/run/error
export SHERMAN_FACE_STARTUP_DIAGNOSTIC=$TMP_DIR/run/startup-diagnostic
export SHERMAN_FACE_SPI_DEVICE=/dev/null
export SHERMAN_FACE_PROC_ROOT=$TMP_DIR/proc
export SHERMAN_FACE_STARTUP_POLLS=30

reset_fixture() {
    if [ -r "$SHERMAN_FACE_PID_FILE" ]; then
        fixture_pid=$(sed -n '1p' "$SHERMAN_FACE_PID_FILE")
        case "$fixture_pid" in
            ''|*[!0-9]*) ;;
            *) kill -KILL "$fixture_pid" 2>/dev/null || true ;;
        esac
    fi
    rm -rf "$SHERMAN_FACE_PROC_ROOT"
    mkdir -p "$SHERMAN_FACE_PROC_ROOT"
    rm -f "$SHERMAN_FACE_PID_FILE" "$SHERMAN_FACE_HEALTH_FILE" \
        "$SHERMAN_FACE_ERROR_FILE" "$SHERMAN_FACE_STARTUP_DIAGNOSTIC"
}

export FAKE_FACE_SCENARIO=delayed
export FAKE_FACE_READY_DELAY_S=0.35
"$INIT_SCRIPT" start >"$TMP_DIR/delayed.out" 2>&1
grep 'started sherman-face' "$TMP_DIR/delayed.out" >/dev/null
grep '"personality_backend":"native-personality-c-v1"' \
    "$SHERMAN_FACE_HEALTH_FILE" >/dev/null
"$INIT_SCRIPT" status >"$TMP_DIR/status.out"
grep 'sherman-face is running' "$TMP_DIR/status.out" >/dev/null
"$INIT_SCRIPT" stop >"$TMP_DIR/stop.out"
grep 'stopped sherman-face' "$TMP_DIR/stop.out" >/dev/null

reset_fixture
export FAKE_FACE_SCENARIO=early-exit
export FAKE_FACE_READY_DELAY_S=0
if "$INIT_SCRIPT" start >"$TMP_DIR/early.out" 2>&1; then
    echo "expected early-exit startup to fail" >&2
    exit 1
fi
grep 'exited before publishing readiness' "$TMP_DIR/early.out" >/dev/null
grep 'fixture personality loader failed' "$TMP_DIR/early.out" >/dev/null
grep 'fixture personality loader failed' "$SHERMAN_FACE_STARTUP_DIAGNOSTIC" \
    >/dev/null
[ "$(wc -c <"$SHERMAN_FACE_STARTUP_DIAGNOSTIC" | tr -d '[:space:]')" -le 4096 ]
[ ! -e "$SHERMAN_FACE_PID_FILE" ]

reset_fixture
export FAKE_FACE_SCENARIO=degraded
if "$INIT_SCRIPT" start >"$TMP_DIR/degraded.out" 2>&1; then
    echo "expected degraded personality readiness to fail" >&2
    exit 1
fi
grep 'published non-production readiness' "$TMP_DIR/degraded.out" >/dev/null
grep '"personality_degraded":true' "$SHERMAN_FACE_STARTUP_DIAGNOSTIC" \
    >/dev/null
[ ! -e "$SHERMAN_FACE_PID_FILE" ]

reset_fixture
export FAKE_FACE_SCENARIO=oversized
export SHERMAN_FACE_STARTUP_POLLS=3
if "$INIT_SCRIPT" start >"$TMP_DIR/oversized.out" 2>&1; then
    echo "expected oversized health record to fail" >&2
    exit 1
fi
grep 'readiness timed out' "$TMP_DIR/oversized.out" >/dev/null
[ "$(wc -c <"$SHERMAN_FACE_STARTUP_DIAGNOSTIC" | tr -d '[:space:]')" -le 4096 ]
[ ! -e "$SHERMAN_FACE_PID_FILE" ]
export SHERMAN_FACE_STARTUP_POLLS=30

reset_fixture
mv "$SHERMAN_PERSONALITY_LIBRARY" "$SHERMAN_PERSONALITY_LIBRARY.missing"
if "$INIT_SCRIPT" start >"$TMP_DIR/missing-library.out" 2>&1; then
    echo "expected missing personality library preflight to fail" >&2
    exit 1
fi
grep "missing $SHERMAN_PERSONALITY_LIBRARY" \
    "$TMP_DIR/missing-library.out" >/dev/null
[ ! -e "$SHERMAN_FACE_PID_FILE" ]
mv "$SHERMAN_PERSONALITY_LIBRARY.missing" "$SHERMAN_PERSONALITY_LIBRARY"

echo "face-service tests: PASS"
