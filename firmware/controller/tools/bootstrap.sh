#!/bin/sh
# Fetch only the audited SDK revision; toolchain installation is separate.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
sdk="$root/.cache/pico/sdk"
revision=a1438dff1d38bd9c65dbd693f0e5db4b9ae91779
if [ ! -d "$sdk/.git" ]; then
  mkdir -p "$(dirname "$sdk")"
  git clone --branch 2.2.0 --depth 1 https://github.com/raspberrypi/pico-sdk.git "$sdk"
fi
[ "$(git -C "$sdk" rev-parse HEAD)" = "$revision" ] || {
  echo 'SDK revision mismatch; preserve the existing checkout and use a separate SDK path.' >&2
  exit 1
}
[ -z "$(git -C "$sdk" status --porcelain --untracked-files=no)" ] || {
  echo 'SDK has local changes; refusing to overwrite them.' >&2
  exit 1
}
git -C "$sdk" submodule update --init lib/tinyusb
