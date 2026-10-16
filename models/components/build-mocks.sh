#!/usr/bin/env bash

set -euo pipefail

component_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if ! command -v openscad >/dev/null 2>&1; then
  printf 'OpenSCAD is required to rebuild the component mocks.\n' >&2
  exit 1
fi

openscad \
  -o "$component_dir/stl/luckfox-pico-ultra-w-envelope.stl" \
  "$component_dir/source/luckfox-pico-ultra-w-envelope.scad"
openscad \
  -o "$component_dir/stl/sc3336-camera-b-envelope.stl" \
  "$component_dir/source/sc3336-camera-b-envelope.scad"
openscad \
  -o "$component_dir/stl/pololu-4762-encoder-cable-envelope.stl" \
  "$component_dir/source/pololu-4762-encoder-cable-envelope.scad"
openscad \
  -o "$component_dir/stl/adafruit-4755-bq24074-envelope.stl" \
  "$component_dir/source/adafruit-4755-bq24074-envelope.scad"
openscad \
  -o "$component_dir/stl/godiymodules-i2chub-envelope.stl" \
  "$component_dir/source/godiymodules-i2chub-envelope.scad"
openscad \
  -o "$component_dir/stl/sherman-charging-interlock-rev-a-envelope.stl" \
  "$component_dir/source/sherman-charging-interlock-rev-a-envelope.scad"
openscad \
  -o "$component_dir/stl/sherman-charging-interlock-rev-b-envelope.stl" \
  "$component_dir/source/sherman-charging-interlock-rev-b-envelope.scad"
