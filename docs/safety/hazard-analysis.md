# Preliminary Hazard Analysis

## Scope and disclaimer

This is a prototype risk-reduction plan, not a claim of product certification.
Operate early hardware on a protected bench, current-limited supply, restrained
chassis, and sacrificial test surface. Keep it away from children, pets, liquids,
and fragile objects. Early charge qualification remains supervised; autonomous
dock charging is not released until the charging, interlock, contact, thermal,
fault, and departure evidence is complete.

## Severity and acceptance

Use severity `S0` negligible, `S1` minor equipment/data impact, `S2` meaningful injury/fire/property risk, `S3` severe injury/fire. Probability is `P1` remote through `P4` frequent. Any plausible S2/S3 hazard needs engineered prevention plus detection/recovery; warning text alone is insufficient.

## Hazard register

| Hazard | Causes | Controls | Verification |
| --- | --- | --- | --- |
| Falls from desk | stale/failed cliff sensor, high speed, approach angle, bad surface, Linux stall | controller-owned cliff reflex, command TTL, speed/zone limits, multi-sensor geometry, qualified surfaces | 500-trial protocol, injected stale/fail, angles/speeds/light/battery |
| Pinch/entanglement | wheel access, hair/cable ingestion | recessed wheels, low torque/speed, current limit, guarded gaps, stop on stall | probe/harness tests, stall current/time, recovery |
| Collision/damage | perception miss, localization error, remote command | bounded energy, local proximity, safety arbiter, stop/replan, no pushing task | obstacle matrix and command fuzzing |
| Battery fire/damage | poor cell, short, overcharge, heat, crush, wrong USB/power path | protected cell, reputable source, fuse/protection, qualified load-sharing charger, split motor/compute branches, serviceable enclosure, thermal limits | live-load fault/current/charge/thermal/inspection protocols |
| Charge transition causes motion | input insertion/bounce/removal, rail collapse, resets, back-power, stale command replay | raw-input plus `PGOOD` charge sensing, hardware-ANDed default-off motor gate and driver sleep, fresh-arm requirement, command expiry | active-motion insertion, input bounce/cut, stuck/open interlock faults, independent resets, terminal measurement |
| Thermal burn/component damage | compute/inference, converter, driver, charging | thermal paths, monitoring, workload shedding, charge limits | steady-state worst loads and sensor plausibility |
| Privacy exposure | unintended streaming/logging, compromised Jarvis | raw frames transient by default, authenticated link, privacy mode, bounded diagnostics | data-flow audit, network capture, erase/export tests |
| Unsafe update/config | corrupted image, wrong profile/limits | signed/verified artifact when practical, safe compiled maxima, rollback, disarmed update | corrupt/interrupted update and config fuzz |
| False emotional assurance | cute display hides fault | reserved authoritative fault/stop/privacy overlays | state-expression contract tests |
| Autonomous nuisance | repetitive noise/motion, night operation | quiet hours, duty limits, user pause, routines | 24-hour simulation and endurance observation |

## Safety case structure

For each critical claim, maintain: claim → assumptions → controls → test IDs → evidence → residual risk. Example: “Sherman stops before a qualified desk edge” depends on surface set, speed envelope, sensor height/angle, controller timing, wheel traction, mass distribution, and battery range. The claim is invalid outside those assumptions and Sherman must communicate or restrict unsupported operation.

## Human controls

- A local stop control plus an internal hardware charge interlock that independently
  forces the motor rail off and driver asleep whenever charge input is present or
  uncertain. Neither depends on a user charging step or Linux cooperation.
- An obvious software stop available locally and through Jarvis, but not as a substitute for physical/controller protection.
- Pickup handling: stop/disarm on loss of surface/contact/orientation evidence and require a deliberate re-arm sequence after placement.
- Clear charging, updating, privacy, degraded, and fault expressions.
- Setup flow that characterizes the desk/surface and refuses unqualified motion.

## Release blockers

- Any uncontrolled motor pulse at boot/reset/USB transition.
- Any normal cable-charge workflow that requires shutdown, a switch, disarming,
  shell opening, battery handling, or any action beyond plugging in one exterior
  cable.
- Any dock flow that cannot remove dock power on Sherman's request, prove charger
  input absent, require fresh motion authority, and depart without human help.
- Any single Linux process failure that can sustain motion indefinitely.
- Cliff test failure without a bounded, explained, corrected cause.
- Battery/charger operating outside manufacturer conditions.
- Unbounded camera retention or unauthenticated remote motion request.
- Safety configuration writable beyond compiled/hardware maxima.
