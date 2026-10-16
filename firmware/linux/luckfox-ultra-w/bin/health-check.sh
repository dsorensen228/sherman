#!/bin/sh
# Read-only Luckfox Pico Ultra W bring-up evidence collector.
# It intentionally performs no mounts, writes, GPIO requests, service changes,
# network connections, or device-tree overlay operations.

set -u

FORMAT=text
ROOT=${SHERMAN_HEALTH_ROOT:-}
EXPECTED_SPI_HZ=${SHERMAN_EXPECTED_SPI_HZ:-}
FAILURES=0
WARNINGS=0
CHECKS=0

usage() {
    cat <<'EOF'
Usage: health-check.sh [--format text|ndjson] [--root DIR]

Collect bounded, read-only evidence for the Sherman Luckfox Ultra W baseline.
--root redirects absolute file reads into a fixture tree for host tests.

Environment:
  SHERMAN_HEALTH_ROOT       Same as --root.
  SHERMAN_EXPECTED_SPI_HZ   Expected SPI maximum; default 40000000.
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --format)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            FORMAT=$2
            shift 2
            ;;
        --root)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            ROOT=${2%/}
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [ -z "$EXPECTED_SPI_HZ" ]; then
    EXPECTED_SPI_HZ=40000000
fi

case "$FORMAT" in
    text|ndjson) ;;
    *) echo "Unsupported format: $FORMAT" >&2; exit 2 ;;
esac

path() {
    printf '%s%s' "$ROOT" "$1"
}

read_text() {
    file=$(path "$1")
    if [ -r "$file" ]; then
        tr -d '\000' <"$file" 2>/dev/null | sed -n '1p'
    else
        printf '%s' "unavailable"
    fi
}

json_escape() {
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/	/\\t/g'
}

emit() {
    severity=$1
    name=$2
    expected=$3
    observed=$4
    detail=$5
    CHECKS=$((CHECKS + 1))
    case "$severity" in
        FAIL) FAILURES=$((FAILURES + 1)) ;;
        WARN) WARNINGS=$((WARNINGS + 1)) ;;
    esac

    if [ "$FORMAT" = ndjson ]; then
        printf '{"type":"check","status":"%s","name":"%s","expected":"%s","observed":"%s","detail":"%s"}\n' \
            "$(json_escape "$severity")" \
            "$(json_escape "$name")" \
            "$(json_escape "$expected")" \
            "$(json_escape "$observed")" \
            "$(json_escape "$detail")"
    else
        printf '%-4s %-24s expected=%s observed=%s %s\n' \
            "$severity" "$name" "$expected" "$observed" "$detail"
    fi
}

expect_equal() {
    name=$1
    expected=$2
    observed=$3
    detail=$4
    if [ "$observed" = "$expected" ]; then
        emit PASS "$name" "$expected" "$observed" "$detail"
    else
        emit FAIL "$name" "$expected" "$observed" "$detail"
    fi
}

expect_path() {
    name=$1
    target=$2
    detail=$3
    resolved=$(path "$target")
    if [ -e "$resolved" ]; then
        emit PASS "$name" present present "$detail"
    else
        emit FAIL "$name" present missing "$detail"
    fi
}

cfg_value() {
    key=$1
    cfg=$(path /etc/luckfox.cfg)
    if [ -r "$cfg" ]; then
        sed -n "s/^${key}=//p" "$cfg" | sed -n '1p'
    else
        printf '%s' "unavailable"
    fi
}

process_running() {
    process=$1
    if [ -n "$ROOT" ]; then
        [ -e "$(path "/run/${process}.running")" ]
    elif command -v pidof >/dev/null 2>&1; then
        pidof "$process" >/dev/null 2>&1
    else
        ps 2>/dev/null | grep "[${process%${process#?}}]${process#?}" >/dev/null 2>&1
    fi
}

rtsp_listener_state() {
    if [ -n "$ROOT" ]; then
        if [ -e "$(path /run/rtsp-554.listening)" ]; then
            printf '%s' listening
        else
            printf '%s' not-listening
        fi
    elif command -v ss >/dev/null 2>&1; then
        if ss -lnt 2>/dev/null | grep -E '(^|[.:])554[[:space:]]' >/dev/null 2>&1; then
            printf '%s' listening
        else
            printf '%s' not-listening
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -lnt 2>/dev/null | grep -E '(^|[.:])554[[:space:]]' >/dev/null 2>&1; then
            printf '%s' listening
        else
            printf '%s' not-listening
        fi
    else
        printf '%s' unavailable
    fi
}

stream_evidence_state() {
    if [ -n "$ROOT" ]; then
        if [ -e "$(path /run/camera-streaming)" ]; then
            printf '%s' observed
        else
            printf '%s' not-observed
        fi
    elif dmesg 2>/dev/null | grep -E 'stream ON|start streaming|rkisp queue buf done' >/dev/null 2>&1; then
        printf '%s' observed
    else
        printf '%s' not-observed
    fi
}

face_service_running() {
    if [ -n "$ROOT" ]; then
        [ -e "$(path /run/sherman-face.running)" ]
    elif [ -x /etc/init.d/S99sherman-face ]; then
        /etc/init.d/S99sherman-face status >/dev/null 2>&1
    else
        return 1
    fi
}

board_model=$(read_text /proc/device-tree/model)
emit INFO collector_schema measured "sherman.luckfox.health.v1" "bounded read-only evidence"
collected_at=unavailable
if command -v date >/dev/null 2>&1; then
    collected_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || printf '%s' unavailable)
fi
emit INFO collected_at_utc measured "$collected_at" "runner wall clock"
kernel_release=$(read_text /proc/sys/kernel/osrelease)
emit INFO kernel_release measured "$kernel_release" "target build identity"
uptime_seconds=$(read_text /proc/uptime)
uptime_seconds=${uptime_seconds%% *}
emit INFO uptime_seconds measured "$uptime_seconds" "monotonic boot age"
expect_equal board_model "Luckfox Pico Ultra W" "$board_model" "exact target identity"

expect_equal rgb_parallel "0" "$(cfg_value RGB_ENABLE)" "/etc/luckfox.cfg"
expect_equal spi0_status "1" "$(cfg_value SPI0_M0_STATUS)" "/etc/luckfox.cfg"
expect_equal spi0_cs "1" "$(cfg_value SPI0_M0_CS_ENABLE)" "/etc/luckfox.cfg"
expect_equal spi0_miso "0" "$(cfg_value SPI0_M0_MISO_ENABLE)" "write-only LCD bus"
expect_equal spi0_max_hz "$EXPECTED_SPI_HZ" "$(cfg_value SPI0_M0_SPEED)" "expected configured SPI cap"

expect_equal dt_rgb disabled "$(read_text /proc/device-tree/syscon@ff000000/rgb/status)" "releases shared header pins"
expect_equal dt_panel disabled "$(read_text /proc/device-tree/panel/status)" "parallel RGB panel disabled"
expect_equal dt_spi0 okay "$(read_text /proc/device-tree/spi@ff500000/status)" "SPI0 controller enabled"
expect_equal dt_spidev0 okay "$(read_text /proc/device-tree/spi@ff500000/spidev@0/status)" "userspace display endpoint"
expect_path spi_device /dev/spidev0.0 "display transport"
expect_path gpiochip1 /dev/gpiochip1 "DC/RST/BL control lines"
expect_path spi_overlay /sys/kernel/config/device-tree/overlays/spi0m0 "startup overlay replayed"

expect_equal dt_sc3336 okay "$(read_text /proc/device-tree/i2c@ff470000/sc3336@30/status)" "camera sensor"
expect_equal dt_csi2_dphy0 okay "$(read_text /proc/device-tree/csi2-dphy0/status)" "CSI receiver"
expect_path media0 /dev/media0 "camera media graph"
expect_path video0 /dev/video0 "CIF capture node"

if process_running rkipc; then
    emit PASS rkipc_process running running "vendor camera/ISP pipeline"
else
    emit FAIL rkipc_process running stopped "vendor camera/ISP pipeline"
fi

rtsp_state=$(rtsp_listener_state)
case "$rtsp_state" in
    listening) emit PASS rtsp_554 listening listening "run probe-rtsp.sh for decoded-frame evidence" ;;
    unavailable) emit WARN rtsp_554 listening unavailable "neither ss nor netstat is installed" ;;
    *) emit FAIL rtsp_554 listening "$rtsp_state" "vendor RTSP service" ;;
esac

stream_state=$(stream_evidence_state)
if [ "$stream_state" = observed ]; then
    emit PASS camera_stream observed observed "bounded kernel-log predicate"
else
    emit WARN camera_stream observed "$stream_state" "kernel ring may have rotated; use RTSP probe"
fi

if face_service_running; then
    emit PASS face_service running running "personality-driven display service"
else
    emit FAIL face_service running stopped "personality-driven display service"
fi

face_health_file=$(path /run/sherman-face.health.json)
face_health=unavailable
if [ -r "$face_health_file" ]; then
    face_health=$(dd if="$face_health_file" bs=4097 count=1 2>/dev/null)
fi
face_health_bytes=$(printf '%s' "$face_health" | wc -c | tr -d ' ')
if [ "$face_health" != unavailable ] \
    && [ "$face_health_bytes" -le 4096 ] \
    && printf '%s' "$face_health" | grep -F '"state":"running"' >/dev/null 2>&1; then
    emit PASS face_health running running "bounded /run health record"
else
    emit FAIL face_health running unavailable "missing, oversized or stale face health"
fi
if printf '%s' "$face_health" | grep -F '"mode":"personality"' >/dev/null 2>&1; then
    emit PASS face_mode personality personality "production boot mode"
else
    emit FAIL face_mode personality diagnostic-or-unavailable "demo/manual must be explicit"
fi
if printf '%s' "$face_health" | grep -F '"personality_degraded":false' >/dev/null 2>&1; then
    emit PASS personality_runtime native native "versioned native personality active"
elif printf '%s' "$face_health" | grep -F '"personality_degraded":true' >/dev/null 2>&1; then
    emit WARN personality_runtime native safe-calm-fallback "inspect personality_last_error"
else
    emit FAIL personality_runtime native unavailable "personality health field missing"
fi

temperature=$(read_text /sys/class/thermal/thermal_zone0/temp)
emit INFO soc_temperature_millicelsius measured "$temperature" "no release limit frozen yet"

mem_total=unavailable
meminfo=$(path /proc/meminfo)
if [ -r "$meminfo" ]; then
    mem_total=$(sed -n 's/^MemTotal:[[:space:]]*\([0-9][0-9]*\)[[:space:]]*kB.*/\1/p' "$meminfo" | sed -n '1p')
    [ -n "$mem_total" ] || mem_total=unavailable
fi
emit INFO mem_total_kib measured "$mem_total" "resource evidence"

if [ "$FAILURES" -eq 0 ]; then
    overall=PASS
else
    overall=FAIL
fi

if [ "$FORMAT" = ndjson ]; then
    printf '{"type":"summary","status":"%s","checks":%s,"failures":%s,"warnings":%s}\n' \
        "$overall" "$CHECKS" "$FAILURES" "$WARNINGS"
else
    printf '%s\n' "summary status=$overall checks=$CHECKS failures=$FAILURES warnings=$WARNINGS"
fi

[ "$FAILURES" -eq 0 ]
