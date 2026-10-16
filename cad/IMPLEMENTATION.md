# CAD Implementation Plan

## Repository layout when artifacts begin

- `components/`: measured/vendor part models with source/revision/measurement notes.
- `layout/`: M0 bounding boxes and alternative arrangements.
- `chassis/`: lower tray, motor/axle/skid, compute tray and mounts.
- `face/`: display cassette, window, camera/ToF apertures and baffles.
- `shell/`: cosmetic/service enclosure aligned with concept intent.
- `dock/`: only after Phase 4 go decision.
- `drawings/`, `exports/`, `print-profiles/`, `assembly/`.

## Parameter ledger

Central parameters: board/connector envelopes, wheel diameter/track/axle, ground clearance, footprint, shell thickness/ribs, component clearances, cable bend/service volumes, optical origins/FOV, cliff sensor height/angle/edge detect geometry, battery swelling, fastener/insert, ventilation, print tolerances and mass.

Each critical parameter links to measurement/source and owning requirement. Avoid copied magic dimensions across files.

## Design ladder

### M0 layout

Model all components as conservative bounding boxes plus connector/optical/service volumes. Compare horizontal vs stacked board, battery location, motor orientation, wheel protrusion and display/camera arrangement. Report envelope/mass/CoM/unused volume and collisions; do not add cosmetic shell.

### M1 open tray

Mount board, motors, controller/driver/sensors with maximum visibility/access. Validate fastener/tool path, shaft/axle/wheel, wiring, recovery USB, antenna, and measured thermal/power tests. Use temporary adjustable sensor mounts.

### M2 restrained mobile chassis

Rigid drivetrain geometry, retained harness, cliff mounts, skid, battery dummy/qualified power. Add bump/edge test protection and tether point. Publish robot frame/datum and measured as-built geometry for calibration.

### M3 serviceable enclosure

Compute tray, removable face cassette, battery replacement path, motor disable access, thermal/vent features, optical window/baffles, wheel guards and cleanability. Ten assembly cycles.

### M4/M5 refinement/release

Apply concept language—rounded ivory shell/graphite lower chassis/black face—without compromising evidence. Tolerance study, print orientation/material/profile, drawings, assembly/inspection, exports and release tag.

## Design reviews

At every ladder step review collisions/service motion, optical FOV and window, cliff stopping geometry, drive support polygon/CoM/tip, antenna, heat/battery separation, motor noise/vibration, harness abrasion/strain, debris/hair gaps, fastener access, printability and actual measured envelope/mass.

## Agent work partition

Separate agents may own component library, M0 layout alternatives, drivetrain tray, face/optics, shell/serviceability and release automation after shared parameters/interfaces are frozen. One CAD integrator owns the top assembly and parameter ledger.

