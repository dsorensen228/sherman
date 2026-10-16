# Procedural Eyes

Sherman's `320 × 170` face renderer is a focused, attributed subset of the
MIT-licensed [pycozmo](https://github.com/zayfod/pycozmo) procedural-face
engine. It uses the same 43-parameter Cozmo-style pose and Pillow geometry,
with the robot protocol, numpy dependency, random generator and hardware access
removed. This lets the code run unchanged on the Luckfox's existing Python and
Pillow installation.

The result is deliberately cartoony: two rounded, squashable eyes with readable
eyelids and gaze, no realistic iris or pupil. The canonical output is purple
`#B266FF` (`0xB33F` in RGB565) on black. `render_rgb565()` returns exactly
`108,800` row-major, big-endian bytes for a full display frame; the SPI backend
owns transfer, orientation and GPIO.

`AnimationInputs` covers calm, curious, focused, pleased, uncertain,
frustrated, tired and surprised expressions plus continuous gaze, blink,
attention and arousal. This module owns no clock or randomness, so the caller
can reproduce every frame.

`sherman_procedural_eyes` is the exact Pillow reference renderer and source of
golden images. `cpp/` provides the target path: a dependency-free C++17 scanline
renderer with the same 43-value pose order, expression presets and big-endian
RGB565 contract. It avoids full-frame Pillow allocations while retaining the
same rounded shapes, asymmetric corner controls, lids, squash/stretch and gaze.
The C++ API renders into caller-owned memory; `procedural_eyes_c.h` exposes the
same path as a stable no-allocation C ABI suitable for `ctypes`. The frame CLI
accepts the expression and every continuous input, writing one raw frame to a
file or stdout. Neither path knows about SPI or GPIO.

Test and inspect:

```sh
PYTHONPATH=display/procedural_eyes python3 -m unittest discover \
  -s display/procedural_eyes/tests -v
python3 display/procedural_eyes/tools/render_gallery.py /tmp/sherman-eyes.png
python3 display/procedural_eyes/tools/benchmark.py
cmake -S display/procedural_eyes/cpp -B /tmp/sherman-eyes-cpp
cmake --build /tmp/sherman-eyes-cpp --config Release
ctest --test-dir /tmp/sherman-eyes-cpp --output-on-failure
/tmp/sherman-eyes-cpp/procedural_eyes_benchmark
/tmp/sherman-eyes-cpp/procedural_eyes_render_frame \
  --expression curious --gaze-x 0.7 --attention 1 --output /tmp/eye.rgb565
python3 display/procedural_eyes/tools/compare_renderers.py \
  /tmp/sherman-eyes-cpp/procedural_eyes_render_frame
```

## Measured target result

On the Luckfox Pico Ultra W (`armv7l`, Buildroot, vendor GCC 8.3 cross
toolchain), 2,000 full `320 × 170` render-and-pack frames measured `2.278 ms`
mean and `3.980 ms` p95. Calling the shared library from the target's Python
3.11 through `ctypes` measured `2.687 ms` mean and `4.439 ms` p95 over 1,000
frames, using one reused 108,800-byte output buffer. These figures exclude SPI
transfer time. The unoptimized Pillow reference measured about `39.8 ms` for
the same render-and-pack stage on target.

For the eight canonical still poses, mask intersection-over-union between the
fast renderer and exact Pillow reference ranges from `0.8930` to `0.9782`.
Both paths share parameter ordering, colors and inputs; Pillow remains the
golden renderer while C++ is the realtime target path.

FluxGarage RoboEyes was evaluated but not copied: it is GPL-3.0 and tied to
Arduino/Adafruit GFX. Grobot_Animations is MIT and TFT-oriented, but its current
v0.1.5 implementation is ESP32-only and substantially less mature than
pycozmo's Linux renderer.
