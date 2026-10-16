# Display Testing Plan

## Logic/timeline

Fake-clock tests for every clip entry/hold/exit, interpolation endpoints, priority/preemption, rapid state churn, canceled action, overlay latch/clear, brightness policy and reduced-motion alternative. Property tests keep geometry/brightness finite/in bounds and guarantee authoritative overlay wins.

## Golden visual tests

Render selected semantic checkpoints at canonical resolutions/themes into approved images plus structural metrics (eye centers, openness, gaze). Tolerate intended renderer differences carefully; semantic tests are primary. Review changed goldens visually and record reason.

## Legibility

Blinded clips/stills for core states; collect label/confidence and confusion matrix. Require near-perfect recognition for fault/privacy/critical battery/charging/update and agreed baseline for nuanced mood. Test desk-distance, viewing angles, ambient light, quick glance and display brightness/night.

## Target performance

On the Waveshare 1.9-inch `320 × 170` candidate, measure semantic-event→render→visible latency with a GPIO marker plus high-speed camera or photodiode where practical; frame pacing; tearing; CPU/RSS; bytes and transactions per frame; SPI clock; full/dirty region ratio; drops/errors; boot-to-first-safe-frame; power/thermal; and interaction with camera/ToF/motors/network.

Initial gates: `≥30` stable visible fps for the canonical eye workload, `≤50 ms` semantic-to-visible for blink/gaze and authoritative overlays, no stale-frame queue growth, and no persistent visible corruption. Record results at 16/24/32/40 MHz and test 50 MHz only if the panel/harness edges and error record justify it.

## Failure/endurance

Missing/unplugged/stalled/slow display, SPI/bus errors, wrong dimensions/rotation, reset during transfer, renderer crash/restart, rapid overlay, config/theme corruption, full resource pressure and shutdown. Execute 100 cold boots, connector disturbance only on an unpowered system, and camera/ToF/storage/network concurrency. Eight/24-hour eye animation checks leaks, image retention, stuck pixels/frame and repetition.

## Mechanical/optical

Final window tests for reflections, contrast, color, light leak into camera/ToF, active-area alignment to the `42.72 × 22.70 mm` visible region, faceplate reassembly and cleanability. Test display, camera, and ToF windows separately before considering a shared cosmetic layer. Concept art is not acceptance evidence.
