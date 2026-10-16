#!/bin/sh
# Deploy independently of /opt/sherman so face upgrades cannot erase speech.
set -eu
TARGET=${1:-robot-host}
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/../../../.." && pwd)
CONFIG_SOURCE=${2:-$SCRIPT_DIR/../config/banter.json}
STAGE=/tmp/sherman-banter-deploy.$$
ssh "$TARGET" "mkdir -p '$STAGE'"
trap 'ssh "$TARGET" "rm -rf '\''$STAGE'\''" >/dev/null 2>&1 || true' EXIT HUP INT TERM
tar -C "$REPO_ROOT/personality" --exclude='__pycache__' --exclude='tests' -cf - banter \
    | ssh "$TARGET" "tar -xf - -C '$STAGE'"
scp -q "$CONFIG_SOURCE" "$TARGET:$STAGE/banter.json"
scp -q "$SCRIPT_DIR/../init/S99sherman-banter" "$TARGET:$STAGE/init"
ssh "$TARGET" sh -s -- "$STAGE" <<'REMOTE'
set -eu
stage=$1
app=/opt/sherman-banter
init=/etc/init.d/S99sherman-banter
config=/etc/sherman/banter.json
# Preserve provisioned config. An explicit config update is a separate operation.
if [ -f "$config" ]; then cp -p "$config" "$stage/banter.json"; fi
python3 "$stage/banter/run_banter.py" --config "$stage/banter.json" --check
was_running=0
had_app=0
had_init=0
had_config=0
[ ! -d "$app" ] || had_app=1
if [ -f "$init" ]; then
    cp -p "$init" "$stage/previous.init"
    had_init=1
    if "$init" status >/dev/null 2>&1; then was_running=1; fi
fi
if [ -f "$config" ]; then cp -p "$config" "$stage/previous.config"; had_config=1; fi
if [ "$had_init" -eq 1 ]; then "$init" stop; fi
rm -rf "$app.previous"
if [ "$had_app" -eq 1 ]; then mv "$app" "$app.previous"; fi
rollback() {
    "$init" stop >/dev/null 2>&1 || true
    rm -rf "$app"
    if [ "$had_app" -eq 1 ]; then mv "$app.previous" "$app"; fi
    if [ "$had_init" -eq 1 ]; then cp -p "$stage/previous.init" "$init"; else rm -f "$init"; fi
    if [ "$had_config" -eq 1 ]; then cp -p "$stage/previous.config" "$config"; else rm -f "$config"; fi
    if [ "$was_running" -eq 1 ]; then "$init" start; fi
}
install_new() {
    mkdir -p "$app" /etc/sherman /userdata/sherman || return 1
    cp -R "$stage/banter" "$app/" || return 1
    cp "$stage/init" "$init" || return 1
    cp "$stage/banter.json" "$config" || return 1
    chmod 0755 "$init" || return 1
    chmod 0644 "$config" || return 1
    "$init" start || return 1
    "$init" status || return 1
}
if ! install_new; then
    rollback
    echo 'banter deployment failed; previous deployment restored' >&2
    exit 1
fi
REMOTE
echo "deployed Sherman banter to $TARGET"
