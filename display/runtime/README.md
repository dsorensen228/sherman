# Face runtime

`run_face.py` combines the clock-free procedural renderer with natural blinks,
smooth semantic-expression transitions, and the bounded ST7789 backend. Its
production mode consumes the versioned native personality C ABI and presents
the resulting expression, idle micro-behavior, gaze, eyelid, attention and
arousal semantics. Personality owns character policy; this layer owns only
scheduling, validation, persistence and animation/presentation.

The default mode is autonomous `personality`, not an expression demo. The
target service loads `/etc/sherman/face-runtime.json`, runs personality at a
bounded 10 Hz and the display at 30 fps, drops stale ticks/frames instead of
queueing, and stores a checksummed native emotion/idle, behavior-policy and
routine-progress snapshot in
`/userdata/sherman/personality.state`. The state envelope and health record are
each bounded to 4096 bytes. State is written at most at the configured interval
and once during orderly shutdown.

Production invocation:

```sh
PYTHONPATH=display:display/procedural_eyes \
  SHERMAN_EYES_LIBRARY=/opt/sherman/lib/libsherman_procedural_eyes_c.so \
  SHERMAN_PERSONALITY_LIBRARY=/opt/sherman/lib/libsherman_personality_c.so \
  python3 display/runtime/run_face.py \
    --config /etc/sherman/face-runtime.json
```

The adapter validates the personality API version and every C structure size
before creating the runtime. Invalid inputs/outputs, time regression or a
runtime failure produce safe calm idle eyes and a degraded health record. Set
`personality_required` for qualification runs that should exit instead. The
input-provider boundary is hardware-independent: camera, presence, task,
attention and future core events can be connected through validated semantic
inputs/`apply_event` without putting policy in the display process. Until those
producers are connected, native personality
owns a fully autonomous stationary idle lifecycle and receives time-of-day plus
zero-valued external stimuli.

Circadian behavior is marked valid only when an explicit POSIX `timezone` is
configured. The bench profile uses
`EST5EDT,M3.2.0/2,M11.1.0/2`; no timezone is embedded in personality logic.

Manual and vocabulary-cycle behavior remain explicit diagnostics:

```sh
python3 display/runtime/run_face.py --renderer reference \
  --mode manual --expression pleased
python3 display/runtime/run_face.py --renderer reference --mode demo
```

The display loop is deadline-based and never queues frames. If render/transfer
misses a deadline, it counts and skips the stale deadline. SIGINT/SIGTERM turns off the
backlight and panel through the backend cleanup path. Normal frames update a
fixed `264 × 162` region enclosing every bounded eye pose; startup and the
`--full-frame` diagnostic path still clear/write the complete panel.

Host animation, ABI, persistence, configuration and scheduler tests:

```sh
PYTHONPATH=display:display/procedural_eyes \
  python3 -m unittest discover -s display/runtime/tests -v
```
