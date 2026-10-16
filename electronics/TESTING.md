# Electronics Testing Plan

## Inspection and bench

Unpowered continuity/no-shorts/polarity; protected first power; coarse module idle/active current and heat; connector pinout; reset behavior; isolation/back-power. Use software counters, inexpensive meters/analyzers and photos first. Retain specialty captures only when borrowed equipment was needed to resolve a concrete system fault.

## Motor/power faults

Driver enable/reset/sleep/fault, open/shorted/disconnected motor only through safe fixture, controlled stall pulse/current limit, simultaneous acceleration/reverse, bulk capacitance, rail sag, thermal protection and recovery. Never exceed exact component/motor conditions.

## Battery/charger

Qualified cell inspection, protection cutoff, converter efficiency across cell/load, undervoltage ramp and sudden disconnect, cable/dock+battery+charger state matrix, reverse current, live-load termination, contact resistance/heat, enclosure thermal, runtime/reserve, and repeated low-battery/boot prevention. Cable insertion is the only V1 user action: it must automatically force both the motor-power gate off and DRV8833 `nSLEEP` low in hardware while compute remains responsive. Test active-motion insertion, input bounce/undervoltage, interlock open/short faults, independent resets, plug removal without command replay, contact loss/misalignment/bridge/short, dock power release, autonomous departure, and all charger fault indications.

## Noise coexistence

Stress motors/boost/charger while camera, ToF, display, UART, encoders and I2C run. Correlate errors/dropouts with current/ripple/ground. Test Wi-Fi if enclosure/antenna/power layout changes.

## Harness/mechanical

Tug/strain, mating cycles, flex through assembly, wheel/edge clearance, connector keying, accidental misconnection analysis and service access. Inspect after endurance for abrasion, heat, loose fasteners/connectors and cell damage.

## Release evidence

Exact BOM/harness revision, tools actually used, available voltage/current/temperature notes or tables, fault results, safety-stop evidence, runtime/charge notes, photographs and allowed substitutions. Produce plots or high-resolution captures only when the underlying problem genuinely needs them.

For replaced inexpensive modules, evidence is the receiving record, known-good functional test and affected integration/safety rerun—not a component-level failure analysis.
