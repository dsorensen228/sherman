#!/bin/sh
# Host-side, bounded RTSP frame-decode probe. No frames are retained.

set -eu

TIMEOUT_SECONDS=10
DECODE_FRAMES=3
URL=
FFMPEG=${SHERMAN_FFMPEG:-ffmpeg}
SSH=${SHERMAN_SSH:-ssh}
TMP_DIR=
DECODER_PID=
WATCHDOG_PID=

usage() {
    cat <<'EOF'
Usage: probe-rtsp.sh [--timeout-seconds N] [--frames N] HOST_OR_RTSP_URL

Examples:
  probe-rtsp.sh robot-host
  probe-rtsp.sh --frames 5 rtsp://192.0.2.10/live/1

Requires ffmpeg. The probe uses RTSP-over-TCP and decodes a bounded number of
real video frames to the null muxer. No frames are retained. Compact JSON reports
only the result and frame counts.

Environment:
  SHERMAN_FFMPEG   ffmpeg command or absolute path; default ffmpeg.
  SHERMAN_SSH      ssh command used to resolve host aliases; default ssh.
EOF
}

positive_bounded_integer() {
    value=$1
    maximum=$2
    case "$value" in
        ''|*[!0-9]*) return 1 ;;
    esac
    [ "$value" -gt 0 ] 2>/dev/null && [ "$value" -le "$maximum" ] 2>/dev/null
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --timeout-seconds)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            positive_bounded_integer "$2" 60 || {
                echo "Timeout must be an integer in the range 1..60" >&2
                exit 2
            }
            TIMEOUT_SECONDS=$2
            shift 2
            ;;
        --frames)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            positive_bounded_integer "$2" 300 || {
                echo "Frame count must be an integer in the range 1..300" >&2
                exit 2
            }
            DECODE_FRAMES=$2
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -* )
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
        *)
            [ -z "$URL" ] || { echo "Only one host or URL is accepted" >&2; exit 2; }
            URL=$1
            shift
            ;;
    esac
done

[ -n "$URL" ] || { usage >&2; exit 2; }
command -v "$FFMPEG" >/dev/null 2>&1 || {
    echo "ffmpeg is required for end-to-end RTSP frame decoding" >&2
    exit 2
}

case "$URL" in
    rtsp://*) ;;
    *)
        # Honor the same Host/HostName mapping used by `ssh robot-host`.
        # If ssh is unavailable or has no mapping, its computed HostName is
        # simply the original DNS name.
        RESOLVED_HOST=$URL
        if command -v "$SSH" >/dev/null 2>&1; then
            CONFIGURED_HOST=$("$SSH" -G "$URL" 2>/dev/null | awk '
                $1 == "hostname" { print $2; exit }
            ')
            [ -z "$CONFIGURED_HOST" ] || RESOLVED_HOST=$CONFIGURED_HOST
        fi
        URL="rtsp://${RESOLVED_HOST}/live/0"
        ;;
esac

TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/sherman-rtsp-probe.XXXXXX")
PROGRESS_FILE=$TMP_DIR/progress
TIMED_OUT_FILE=$TMP_DIR/timed-out

cleanup() {
    if [ -n "$WATCHDOG_PID" ]; then
        kill "$WATCHDOG_PID" 2>/dev/null || true
    fi
    if [ -n "$DECODER_PID" ]; then
        kill "$DECODER_PID" 2>/dev/null || true
    fi
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT HUP INT TERM

"$FFMPEG" \
    -hide_banner \
    -loglevel error \
    -nostdin \
    -rtsp_transport tcp \
    -i "$URL" \
    -map 0:v:0 \
    -an -sn -dn \
    -frames:v "$DECODE_FRAMES" \
    -f null /dev/null \
    -progress pipe:1 \
    -nostats \
    >"$PROGRESS_FILE" 2>/dev/null &
DECODER_PID=$!

# Bound connection, I/O, demux and decode with one implementation-independent
# wall-clock watchdog rather than relying on version-specific FFmpeg options.
(
    SLEEP_PID=
    stop_watchdog() {
        if [ -n "$SLEEP_PID" ]; then
            kill "$SLEEP_PID" 2>/dev/null || true
            wait "$SLEEP_PID" 2>/dev/null || true
        fi
        exit 0
    }
    trap stop_watchdog HUP INT TERM

    sleep "$TIMEOUT_SECONDS" &
    SLEEP_PID=$!
    wait "$SLEEP_PID"
    SLEEP_PID=
    if kill -TERM "$DECODER_PID" 2>/dev/null; then
        : >"$TIMED_OUT_FILE"
        sleep 1
        kill -KILL "$DECODER_PID" 2>/dev/null || true
    fi
) &
WATCHDOG_PID=$!

set +e
wait "$DECODER_PID"
DECODE_STATUS=$?
set -e
DECODER_PID=
kill "$WATCHDOG_PID" 2>/dev/null || true
wait "$WATCHDOG_PID" 2>/dev/null || true
WATCHDOG_PID=

DECODED_FRAMES=$(awk -F= '
    $1 == "frame" {
        gsub(/[[:space:]]/, "", $2)
        if ($2 ~ /^[0-9]+$/) frames = $2
    }
    END { print frames + 0 }
' "$PROGRESS_FILE")

if [ "$DECODE_STATUS" -eq 0 ] && [ "$DECODED_FRAMES" -ge "$DECODE_FRAMES" ]; then
    printf '{"status":"PASS","transport":"tcp","requested_frames":%s,"decoded_frames":%s,"retained_frames":0}\n' \
        "$DECODE_FRAMES" "$DECODED_FRAMES"
    exit 0
fi

if [ -e "$TIMED_OUT_FILE" ]; then
    FAILURE=timeout
else
    FAILURE=decode-failed
fi
printf '{"status":"FAIL","reason":"%s","transport":"tcp","requested_frames":%s,"decoded_frames":%s,"retained_frames":0,"ffmpeg_status":%s}\n' \
    "$FAILURE" "$DECODE_FRAMES" "$DECODED_FRAMES" "$DECODE_STATUS" >&2
exit 1
