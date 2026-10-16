# Electronics and Power Integration

## Scope

`electronics/` owns the prototype electrical architecture: power tree, battery/charger/converters/protection, motor driver/module, companion controller module integration, sensors and level shifting, connectors/harness, grounding/decoupling/noise control, test points, wiring diagrams, exact BOM and receiving/inspection records.

The permanent Luckfox development board is an integration constraint. ADR 0005
authorizes only the dedicated charge-interlock PCB in
[`pcb/charging-interlock-rev-b/`](pcb/charging-interlock-rev-b/); it does not
authorize a custom Luckfox carrier or general Sherman motherboard.

## Current prototype wiring

Start with [`wiring-guide-eli5.md`](wiring-guide-eli5.md) at the bench. It gives
the connections in physical assembly order and uses “the Pico” exclusively for
the Raspberry Pi Pico 2 and “the Luckfox” exclusively for the Luckfox Pico
Ultra W.

[`wiring-guide.md`](wiring-guide.md) and
[`prototype-netlist.csv`](prototype-netlist.csv) define revision W1 of the exact
bench harness for the purchased modules. W1 includes the passive I2C hub and the
automatic charge-present motor interlock required for one-action cable charging.
The corresponding pin-level schematic is
[`diagrams/charging-interlock.svg`](diagrams/charging-interlock.svg).
The verified replacement design is
[`pcb/charging-interlock-rev-b/`](pcb/charging-interlock-rev-b/), including its
Gerber ZIP, order-preparation manifest, connector map, and assembly drawing.
Rev A was rejected during receiving review; quarantine those bare boards.
Follow its staged assembly order and stop gates: A/B are released, C requires
verified UART4 M0 enablement, D carries an explicit XSHUT startup caveat, and
E/F/G remain electrically gated pending the measurements listed in the guide.
W1 is not a released mobile harness until every listed qualification gate passes.

## Safety

Bring up with current-limited bench power and motors disconnected as appropriate. Exact voltage domains and module implementation matter; a breakout carrying a familiar IC name is not equivalent to the IC reference design.
