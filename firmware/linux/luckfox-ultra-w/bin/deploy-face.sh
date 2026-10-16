#!/bin/sh
# Deploy the personality-driven face runtime and both cross-built ARM libraries.

set -eu

TARGET=${1:-robot-host}
EYE_LIBRARY=${2:-}
PERSONALITY_LIBRARY=${3:-}
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/../../../.." && pwd)
REMOTE_STAGE=/tmp/sherman-face-deploy.$$

usage() {
    echo "usage: $0 [SSH_TARGET] ARM_RENDERER_LIBRARY ARM_PERSONALITY_LIBRARY" >&2
}

[ -n "$EYE_LIBRARY" ] || { usage; exit 2; }
[ -n "$PERSONALITY_LIBRARY" ] || { usage; exit 2; }
[ -r "$EYE_LIBRARY" ] || { echo "renderer library not readable: $EYE_LIBRARY" >&2; exit 2; }
[ -r "$PERSONALITY_LIBRARY" ] || { echo "personality library not readable: $PERSONALITY_LIBRARY" >&2; exit 2; }

cleanup() {
    ssh "$TARGET" "rm -rf '$REMOTE_STAGE'" >/dev/null 2>&1 || true
}
trap cleanup EXIT HUP INT TERM

ssh "$TARGET" "rm -rf '$REMOTE_STAGE'; mkdir -p '$REMOTE_STAGE/display' '$REMOTE_STAGE/lib'"
scp -q -r \
    "$REPO_ROOT/display/backends" \
    "$REPO_ROOT/display/procedural_eyes" \
    "$REPO_ROOT/display/runtime" \
    "$TARGET:$REMOTE_STAGE/display/"
scp -q "$EYE_LIBRARY" "$TARGET:$REMOTE_STAGE/lib/libsherman_procedural_eyes_c.so"
scp -q "$PERSONALITY_LIBRARY" "$TARGET:$REMOTE_STAGE/lib/libsherman_personality_c.so"
scp -q "$SCRIPT_DIR/../init/S99sherman-face" "$TARGET:$REMOTE_STAGE/S99sherman-face"
scp -q "$SCRIPT_DIR/../config/face-runtime.json" "$TARGET:$REMOTE_STAGE/face-runtime.json"

ssh "$TARGET" sh -s -- "$REMOTE_STAGE" <<'REMOTE_SCRIPT'
set -u

REMOTE_STAGE=$1
APP_DIR=/opt/sherman
PREVIOUS_APP_DIR=/opt/sherman.previous
INIT_SCRIPT=/etc/init.d/S99sherman-face
CONFIG_DIR=/etc/sherman
CONFIG_FILE=$CONFIG_DIR/face-runtime.json
PREVIOUS_INIT_SCRIPT=$REMOTE_STAGE/S99sherman-face.previous
PREVIOUS_CONFIG_FILE=$REMOTE_STAGE/face-runtime.json.previous
NEW_INIT_SCRIPT=$REMOTE_STAGE/S99sherman-face.installing
NEW_CONFIG_FILE=$REMOTE_STAGE/face-runtime.json.installing
STARTUP_DIAGNOSTIC=/run/sherman-face.startup-diagnostic
DEPLOY_FAILURE_DIAGNOSTIC=/run/sherman-face.deploy-failure
previous_app_exists=0
previous_init_exists=0
previous_config_exists=0
previous_was_running=0
app_install_started=0

if [ -e "$INIT_SCRIPT" ]; then
    cp -p "$INIT_SCRIPT" "$PREVIOUS_INIT_SCRIPT" || exit 1
    previous_init_exists=1
    if [ -x "$INIT_SCRIPT" ] && "$INIT_SCRIPT" status >/dev/null 2>&1; then
        previous_was_running=1
    fi
fi
if [ -e "$CONFIG_FILE" ]; then
    cp -p "$CONFIG_FILE" "$PREVIOUS_CONFIG_FILE" || exit 1
    previous_config_exists=1
fi

install_new() {
    app_install_started=1
    rm -f "$DEPLOY_FAILURE_DIAGNOSTIC" || return 1
    mkdir -p "$APP_DIR" || return 1
    cp -R "$REMOTE_STAGE/display" "$REMOTE_STAGE/lib" "$APP_DIR/" || return 1
    cp "$REMOTE_STAGE/S99sherman-face" "$NEW_INIT_SCRIPT" || return 1
    cp "$REMOTE_STAGE/face-runtime.json" "$NEW_CONFIG_FILE" || return 1
    mkdir -p "$CONFIG_DIR" /userdata/sherman || return 1
    chmod 0700 /userdata/sherman || return 1
    chmod 0755 "$NEW_INIT_SCRIPT" "$APP_DIR/display/runtime/run_face.py" || return 1
    chmod 0644 "$APP_DIR/lib/libsherman_procedural_eyes_c.so" \
        "$APP_DIR/lib/libsherman_personality_c.so" "$NEW_CONFIG_FILE" || return 1
    mv "$NEW_CONFIG_FILE" "$CONFIG_FILE" || return 1
    mv "$NEW_INIT_SCRIPT" "$INIT_SCRIPT" || return 1
    "$INIT_SCRIPT" start || return 1
    "$INIT_SCRIPT" status || return 1
}

preserve_deploy_failure() {
    failure_reason=$1
    diagnostic_tmp=$DEPLOY_FAILURE_DIAGNOSTIC.$$
    if [ -r "$STARTUP_DIAGNOSTIC" ]; then
        dd if="$STARTUP_DIAGNOSTIC" of="$diagnostic_tmp" \
            bs=4096 count=1 2>/dev/null || return 1
    else
        printf 'reason: %s\n' "$failure_reason" >"$diagnostic_tmp" || return 1
    fi
    chmod 0600 "$diagnostic_tmp" || return 1
    mv "$diagnostic_tmp" "$DEPLOY_FAILURE_DIAGNOSTIC" || return 1
    echo "bounded failed-deployment diagnostic:" >&2
    dd if="$DEPLOY_FAILURE_DIAGNOSTIC" bs=4096 count=1 2>/dev/null >&2 || true
}

rollback() {
    rollback_failed=0

    if [ -x "$INIT_SCRIPT" ]; then
        "$INIT_SCRIPT" stop >/dev/null 2>&1 || true
    fi
    rm -f "$NEW_INIT_SCRIPT" || rollback_failed=1
    rm -f "$NEW_CONFIG_FILE" || rollback_failed=1
    if [ "$app_install_started" -eq 1 ]; then
        rm -rf "$APP_DIR" || rollback_failed=1
    fi
    if [ "$previous_app_exists" -eq 1 ]; then
        mv "$PREVIOUS_APP_DIR" "$APP_DIR" || rollback_failed=1
    fi

    if [ "$previous_init_exists" -eq 1 ]; then
        cp -p "$PREVIOUS_INIT_SCRIPT" "$INIT_SCRIPT" || rollback_failed=1
    else
        rm -f "$INIT_SCRIPT" || rollback_failed=1
    fi
    if [ "$previous_config_exists" -eq 1 ]; then
        cp -p "$PREVIOUS_CONFIG_FILE" "$CONFIG_FILE" || rollback_failed=1
    else
        rm -f "$CONFIG_FILE" || rollback_failed=1
    fi

    if [ "$previous_was_running" -eq 1 ]; then
        if [ ! -x "$INIT_SCRIPT" ] || ! "$INIT_SCRIPT" start; then
            echo "rollback restored the previous files but could not restart the service" >&2
            rollback_failed=1
        fi
    fi

    [ "$rollback_failed" -eq 0 ]
}

rollback_and_exit() {
    failure_reason=$1
    echo "$failure_reason; restoring the previous deployment" >&2
    if ! preserve_deploy_failure "$failure_reason"; then
        echo "could not preserve failed-deployment diagnostic" >&2
    fi
    if ! rollback; then
        echo "face service deployment rollback was incomplete" >&2
    fi
    exit 1
}

if [ -x "$INIT_SCRIPT" ] && ! "$INIT_SCRIPT" stop; then
    rollback_and_exit "could not stop the previous face service"
fi
if [ "$previous_was_running" -eq 1 ] \
    && "$INIT_SCRIPT" status >/dev/null 2>&1; then
    rollback_and_exit "previous face service did not stop"
fi

if ! rm -rf "$PREVIOUS_APP_DIR"; then
    rollback_and_exit "could not clear the previous rollback directory"
fi
if [ -d "$APP_DIR" ]; then
    if ! mv "$APP_DIR" "$PREVIOUS_APP_DIR"; then
        rollback_and_exit "could not preserve the current application"
    fi
    previous_app_exists=1
fi

if ! install_new; then
    rollback_and_exit "new face service failed"
fi
REMOTE_SCRIPT

echo "deployed Sherman face runtime to $TARGET"
