# ADR 0004: Zero-Touch Charging and Autonomous Dock Departure

**Status:** Accepted

## Context

Sherman is intended to be a persistent desktop robot, not a device whose owner
opens a shell, removes a battery, operates a motor disconnect, shuts down
compute, or performs a checklist before every charge. Those workflows also
prevent the planned dock from charging Sherman and later releasing it to resume
operation autonomously.

The first power-tree draft routed the whole robot through a 1.5 A charger output
and required a manually opened motor service disconnect during charging. That
design fails the product experience even if it is electrically conservative.

## Decision

V1 charging has one user action: connect power to Sherman's exterior charge
port. Cable insertion automatically transitions Sherman to a hardware-enforced
charging state. The installed battery remains connected, the Luckfox and Pico
remain powered and responsive, and no switch, shutdown, disarm command, shell
opening, or battery handling is part of the charging workflow.

The mobile power tree separates compute and motor current after the battery
fuse:

- the charger `BATT/LIPO` connection and fuel gauge remain across the fused
  battery node;
- charger `LOAD/OUT` supplies the compute/logic boost path only;
- a separate fused-battery branch supplies the DRV8833 through an automatic
  high-side motor-power gate, so motor current does not consume the charger's
  load-output budget;
- valid charger input forces both the motor-power gate off and DRV8833
  `nSLEEP` low in hardware;
- Pico firmware provides independent arm requests but cannot override the
  charger-present hardware inhibit;
- every enable input and output is pulled to the motor-off state during reset,
  loss of 3.3 V, broken control wiring, or interlock-board power loss.

The received Adafruit BQ24074 #4755 remains a candidate for the compute-only
power-path branch. Its 1.5 A output limit must pass the measured compute boot,
camera, display, sensing, and accepted charging-workload envelope with margin.
If it fails, the charger/power-path module is replaced with a higher-capacity
part. The charging UX and autonomous-dock requirement are not relaxed.

The first enclosure exposes the charger's USB-C input. The fast-follow dock is
a rear-entry target that Sherman backs into and uses the same charger input
through at least four contacts:

1. ground, arranged first-mate/last-break;
2. dock-switched 5 V charge power;
3. a current-limited pilot/identity contact for stable alignment proof;
4. an open-drain release-request contact.

Dock charge power defaults off. The dock energizes 5 V only after stable pilot
proof. When battery policy says Sherman has enough energy to leave, Sherman
asserts release request; the dock removes 5 V; Sherman independently verifies
charger input is absent; the hardware inhibit clears; the Pico admits a fresh
motion arm; and Sherman drives forward off the dock under battery power. If dock power does not
turn off, Sherman remains motor-disabled and reports the fault.

An internal battery service connector may exist for maintenance, receiving
tests, or repair. It is not user-facing and is never part of normal charging.

## Alternatives

- **Manual motor disconnect or external cutoff:** rejected. It adds a required
  user action and cannot support autonomous departure.
- **System-off charging:** rejected. It prevents a persistent, responsive robot
  and autonomous dock state management.
- **Firmware-only motor disarm:** rejected. Charger insertion must inhibit
  motion even if the Pico or Luckfox is reset, wedged, or running stale code.
- **Always-live two-contact dock:** rejected. It cannot prove stable contact
  before energization or provide a deterministic release handshake.
- **Route motors through #4755 `LOAD/OUT`:** rejected unless measurements prove
  the entire mobile envelope below the module limit with margin; the selected
  architecture avoids consuming that margin with motor current.

## Consequences

Sherman needs a small retained charge-interlock assembly, a second automatic
power gate for the motor branch, charger-input sensing, and additional dock
contacts/control electronics. The power tree, Pico allocation, harness,
shopping list, CAD envelope, fault campaign, and docking protocol all change.

The user experience becomes invariant across cable and dock charging: apply
charge power and Sherman handles the transition. Safety does not depend on the
owner remembering a step.

## Verification

- At least 100 powered cable insert/remove cycles across battery states and
  accepted compute workloads with no reset, motor pulse, back-power, or user
  action beyond plug/unplug.
- Insert charge power during bounded forward, reverse, and turning commands;
  both motor terminals become inactive within the accepted stop bound.
- Repeat with Pico reset, Luckfox reset, stale command, interlock control wire
  open/short, `PGOOD` stuck, input bounce, undervoltage input, and independent
  power-order permutations.
- Prove the motor-power gate and `nSLEEP` inhibit separately; either path alone
  must prevent commanded motion while charge input is present.
- Verify charge termination, unplug/replug continuity, compute responsiveness,
  current margin, and enclosure temperatures with the defined active workload.
- Dock testing covers misalignment, bridged/shorted contacts, pilot bounce,
  dock-controller reset, loss of communications, release request, verified 5 V
  removal, autonomous departure, and failure to remove 5 V.

## Rollback

Individual charger, switch, logic, contact, or dock-controller candidates may
be replaced after failed qualification. Rollback may not reintroduce a charging
checklist, manual motor control, battery removal, system shutdown, or a dock
that cannot release Sherman for autonomous departure.

## Links

- [`electronics/wiring-guide.md`](../../electronics/wiring-guide.md)
- [`electronics/wiring-guide-eli5.md`](../../electronics/wiring-guide-eli5.md)
- [`docs/hardware/power-and-thermal.md`](../hardware/power-and-thermal.md)
- [`docs/testing/acceptance-matrix.md`](../testing/acceptance-matrix.md)
