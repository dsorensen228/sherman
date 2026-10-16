# Mechanical Envelope and CAD Plan

## Envelope policy

- Stretch target: `70 × 60 × 45 mm`.
- Comfortable first chassis: up to `75 × 65 × 50 mm`.
- Target mass: `≤ 180 g`.
- No dimension is frozen until actual modules, connectors, wiring, fasteners, airflow, optical paths, and assembly motion are modeled.

If the safe, serviceable design misses the stretch target, enlarge it and record why. Do not hide collisions with unrealistic cable bends or inaccessible fasteners.

## Datum and coordinate convention

Robot frame: `+X` forward through the display face, `+Y` left, `+Z` upward. Origin begins at the midpoint of the driven wheel axle projected onto the desk plane unless localization testing justifies another definition. CAD, controller telemetry, URDF-like models, calibration, and documentation use this convention.

## Volume budget

Maintain a parametric bounding-box table from measured components:

- Luckfox board and tallest components;
- Ethernet/USB connector bodies and required access/bend volumes;
- Wi-Fi antenna and keep-out;
- Waveshare 1.9-inch display `51.2 × 27.3 mm` carrier, `42.72 × 22.70 mm` active area, controller board, MX1.25 cable/exit/bend, bezel/window tolerance, and viewing cone;
- camera lens barrel, focus/service access, and unobstructed FOV;
- ToF module, optical window, baffle, cover-glass air gap, and FOV;
- motors, gearboxes, encoders, shaft protrusion, wheels, and tire deflection;
- controller/driver/IMU/cliff modules;
- candidate Adafruit 1200 mAh battery `34 × 62 × 5 mm`/23 g plus swelling allowance, charger, `40.6 × 15.2 × 4.6 mm` boost, wires, switch and fuse;
- fasteners, inserts, shell thickness/ribs, and assembly path.

Allocate `10–15%` unclaimed internal volume in the first mobile revision for harness corrections and thermal mitigation.

## Mechanical architecture

Preferred split:

1. **Lower safety/motion tray:** motors, wheels, skid, controller, driver, cliff sensors, power isolation, and low-mounted battery where practical.
2. **Upper compute tray:** Luckfox board on removable standoffs with connector/service access and controlled airflow.
3. **Front expression cassette:** display, window, camera/ToF apertures, baffles, and a removable calibration-preserving mount.
4. **Outer shell:** cosmetic and protective, removable without disturbing drivetrain alignment.

Do not trap the battery between boards or require destructive disassembly for
service. Put the #4755 USB-C connector at the exterior with a keyed opening,
insertion clearance, and strain relief so V1 charging is literally one cable
insertion. The two #2808 boards and 38.10 mm × 24.13 mm revision-A
charge-interlock PCB are internal; they
are not user charging controls. Recovery USB-C, boot/recovery control, test points,
and critical status indication remain service-accessible.

Reserve the fast-follow dock envelope now for at least four keyed contacts:
first-mate/last-break ground, dock-switched 5 V, current-limited pilot/identity,
and open-drain release request. The contact geometry must prevent adjacent bridges,
remain cleanable, accept alignment error, and permit Sherman to back in and drive
away without human assistance.

## Drivetrain geometry

Record wheel diameter, effective rolling radius, track width, axle location, ground clearance, rear/front overhang, skid contact, and center of mass. The cliff sensors must see the surface early enough to stop before the center of mass and support polygon can pass the edge under worst-case speed, latency, tire slip, and tolerance.

Test at multiple approach angles. A sensor configuration that works head-on can fail during arcs or backward motion. Either qualify reverse motion with rear coverage or restrict it by map/speed/trajectory rules.

## Optical design

- Separate camera and ToF optical paths with matte black baffles.
- Avoid display light leaking into sensors.
- Model cover-window transmission at relevant visible/940 nm wavelengths.
- Keep lens and sensor windows cleanable without opening the robot.
- Control reflections from glossy black face material through angle, coatings/material choice, and recessed apertures.
- Verify camera and ToF FOV after final shell/window; bench values without the faceplate do not qualify.

## Thermal and acoustic design

Provide an air path or conductive path from compute and regulators without heating the battery. Avoid vents that expose wheels to debris or create a surveillance-like face. Measure internal air, compute hot spot, regulator, driver, motor, and battery-adjacent temperatures at idle, perception load, continuous eye animation, stalled/recovery motor pulses, and charging.

Motor mounting and shell cavities can amplify gear noise. Use stiff alignment, controlled isolation, PWM-frequency evaluation, and acceleration profiles before adding soft material that could impair alignment or heat.

## CAD release ladder

- `M0`: bounding boxes and layout alternatives only.
- `M1`: open bench tray; motor/board/sensor fit, no cosmetic shell.
- `M2`: restrained mobile chassis; wheel/cliff geometry and harness retention.
- `M3`: serviceable enclosure; thermal and optical windows.
- `M4`: refined concept-aligned shell; tolerance and repeated assembly.
- `M5`: v1 release drawings, BOM, print/manufacturing profiles, assembly and inspection.

## Mechanical tests

- Fit-check every component against scan/caliper dimensions and connector mating path.
- Ten full assemble/disassemble cycles; no stripped insert, damaged cable, or lost calibration beyond limit.
- Wheel alignment, runout, track-width, and chassis-rock measurements.
- Static tilt and tip tests with worst battery/connector configuration.
- Cable tug/strain and wheel-debris checks.
- Bounded desk-height handling/drop tests onto a protected test surface only after electronics are safe.
- Thermal soak and enclosure deformation.
- Optical FOV/occlusion and face-light leak tests.
- Cliff stopping distance across speed, approach angle, surface, ambient light, battery state, and sensor tolerance.
