#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROBE=$SCRIPT_DIR/../bin/probe-rtsp.sh
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/sherman-probe-rtsp-test.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT HUP INT TERM

PASS_FFMPEG=$TMP_DIR/ffmpeg-pass
SHORT_FFMPEG=$TMP_DIR/ffmpeg-short
FAIL_FFMPEG=$TMP_DIR/ffmpeg-fail
HANG_FFMPEG=$TMP_DIR/ffmpeg-hang
FAKE_SSH=$TMP_DIR/ssh-config

cat >"$PASS_FFMPEG" <<'EOF'
#!/bin/sh
printf '%s\n' "$@" >"$SHERMAN_FAKE_ARGS"
printf 'frame=1\nprogress=continue\nframe=3\nprogress=end\n'
EOF
cat >"$SHORT_FFMPEG" <<'EOF'
#!/bin/sh
printf 'frame=1\nprogress=end\n'
EOF
cat >"$FAIL_FFMPEG" <<'EOF'
#!/bin/sh
printf 'frame=0\nprogress=end\n'
exit 42
EOF
cat >"$HANG_FFMPEG" <<'EOF'
#!/bin/sh
exec sleep 10
EOF
cat >"$FAKE_SSH" <<'EOF'
#!/bin/sh
printf 'hostname 192.0.2.10\n'
EOF
chmod 0755 "$PASS_FFMPEG" "$SHORT_FFMPEG" "$FAIL_FFMPEG" "$HANG_FFMPEG" "$FAKE_SSH"

pass_output=$(SHERMAN_FFMPEG="$PASS_FFMPEG" \
    SHERMAN_SSH="$FAKE_SSH" \
    SHERMAN_FAKE_ARGS="$TMP_DIR/pass.args" \
    "$PROBE" --timeout-seconds 2 --frames 3 example.test)
printf '%s\n' "$pass_output" | grep '"status":"PASS"' >/dev/null
printf '%s\n' "$pass_output" | grep '"decoded_frames":3' >/dev/null
printf '%s\n' "$pass_output" | grep '"retained_frames":0' >/dev/null
if printf '%s\n' "$pass_output" | grep 'example.test' >/dev/null; then
    echo "probe output leaked the supplied RTSP endpoint" >&2
    exit 1
fi
grep '^-f$' "$TMP_DIR/pass.args" >/dev/null
grep '^null$' "$TMP_DIR/pass.args" >/dev/null
grep '^/dev/null$' "$TMP_DIR/pass.args" >/dev/null
grep '^-frames:v$' "$TMP_DIR/pass.args" >/dev/null
grep '^3$' "$TMP_DIR/pass.args" >/dev/null
grep '^rtsp://192.0.2.10/live/0$' "$TMP_DIR/pass.args" >/dev/null

if SHERMAN_FFMPEG="$SHORT_FFMPEG" \
    "$PROBE" --timeout-seconds 2 --frames 3 example.test \
    >"$TMP_DIR/short.out" 2>&1; then
    echo "expected a short decode to fail" >&2
    exit 1
fi
grep '"reason":"decode-failed"' "$TMP_DIR/short.out" >/dev/null
grep '"decoded_frames":1' "$TMP_DIR/short.out" >/dev/null

if SHERMAN_FFMPEG="$FAIL_FFMPEG" \
    "$PROBE" --timeout-seconds 2 --frames 3 example.test \
    >"$TMP_DIR/fail.out" 2>&1; then
    echo "expected ffmpeg failure to fail the probe" >&2
    exit 1
fi
grep '"ffmpeg_status":42' "$TMP_DIR/fail.out" >/dev/null

started=$(date +%s)
if SHERMAN_FFMPEG="$HANG_FFMPEG" \
    "$PROBE" --timeout-seconds 1 --frames 3 example.test \
    >"$TMP_DIR/timeout.out" 2>&1; then
    echo "expected hung decoder to time out" >&2
    exit 1
fi
elapsed=$(( $(date +%s) - started ))
[ "$elapsed" -le 3 ] || { echo "watchdog exceeded its bound" >&2; exit 1; }
grep '"reason":"timeout"' "$TMP_DIR/timeout.out" >/dev/null

if SHERMAN_FFMPEG="$PASS_FFMPEG" \
    "$PROBE" --frames 0 example.test >"$TMP_DIR/invalid.out" 2>&1; then
    echo "expected zero frames to be rejected" >&2
    exit 1
fi
grep 'range 1..300' "$TMP_DIR/invalid.out" >/dev/null

echo "probe-rtsp tests: PASS"
