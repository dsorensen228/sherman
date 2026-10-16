# ADR 0003: Landscape SPI Face Display

## Status

Proposed — candidate selected for procurement; acceptance requires Phase 1 qualification.

## Context

Sherman's target enclosure is roughly 60–65 mm across the face. The directly documented Luckfox RGB panels are 4-inch square modules with roughly 84 mm outlines, so they cannot produce the intended pocket-size desktop character. Earlier planning mentioned 1.3–1.5-inch square displays, but a square canvas wastes vertical area and compresses the horizontal spacing needed for two expressive eyes.

The display must also work with the permanent Luckfox Pico Ultra W, coexist with CSI camera and other buses, boot reproducibly, provide prompt authoritative overlays, and fit behind a serviceable face cassette.

## Decision

Procure two Waveshare 1.9inch LCD Modules, SKU 23822, and qualify one exact hardware/software path:

- landscape `320 × 170` rendering;
- ST7789V2 over 4-wire SPI;
- initial user-space `/dev/spidev0.0` backend with explicit `CS/DC/RST/BL` control;
- RGB display pin reservation disabled and the exact SPI pin group selected in the Luckfox device tree;
- stale display frames dropped, not queued;
- separate visible display window and camera/ToF apertures.

The selection is a Phase 1 candidate, not a production freeze. The initial target is at least 30 stable visible frames/s for the eye workload and at most 50 ms semantic-event-to-visible latency, subject to resource and power review.

## Alternatives

- **Luckfox 4-inch RGB panel:** rejected for the target enclosure.
- **1.3–1.54-inch square ST7789 panels:** rejected as the default shape; two-eye composition and product proportions are poor.
- **Waveshare 1.47-inch landscape panel:** retained as a smaller mechanical fallback if the 1.9-inch carrier cannot fit.
- **Adafruit 1.9-inch product 5394:** retained as a bench fallback; its `57.2 × 36.6 mm` carrier leaves too little enclosure margin.
- **Monochrome OLED:** not selected because color/brightness/expression flexibility outweigh its black-level advantage; lifetime remains a concern.
- **Custom RGB or MIPI display:** deferred until volume/cost justify custom electronics and driver work.

## Consequences

- The face composition now has a real `1.88:1` canvas and a `51.2 × 27.3 mm` carrier envelope.
- Phase 1 owns a Luckfox-specific SPI/backend qualification rather than relying on the 4-inch vendor kit.
- SPI traffic and CPU cost become explicit resource budgets.
- CAD can model a removable display cassette, cable exit, bezel, and actual active-area datum.
- A duplicate primary module supports bench and chassis work in parallel without introducing a second driver target.
- This ADR may be superseded if testing demonstrates an electrical, Linux, optical, supply, or enclosure failure.

## Verification

Follow `docs/hardware/display-selection.md` and `display/TESTING.md`. Archive receiving data, device-tree diff, driver source/build, SPI captures, visible-latency video, CPU/RSS/power numbers, optical results, soak results, and the G1 disposition.

## Rollback

First try the 1.47-inch Waveshare landscape module if the failure is purely mechanical. If the failure is platform throughput or reliability, compare a maintained kernel backend and the Adafruit carrier on an open bench. Reopen the face technology/envelope decision if no path passes; do not adopt the 4-inch display by default.

## Links

- [Selection and qualification plan](../hardware/display-selection.md)
- [Waveshare 1.9-inch product](https://www.waveshare.com/1.9inch-lcd-module.htm)
- [Luckfox device-tree guide](https://wiki.luckfox.com/Luckfox-Pico-Ultra/Device-Tree/)
- [Phase 1 plan](../roadmap/phase-1-brain.md)
