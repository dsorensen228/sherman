# Hardware Planning Index

Hardware is not frozen by this planning pass. Exact orderable parts advance through: `idea → candidate → bench-qualified → integration-qualified → frozen`. Only `frozen` parts are dependencies for release CAD or production configuration.

Read:

- `bom.md` — candidate bill of materials and qualification gates.
- `shopping-list.md` — complete phased prototype order list, quantities, prices, consumables, tooling, and receiving checks.
- `shopping-list.csv` — machine-readable exact module/electromechanical candidate lines from the full shopping list.
- `display-selection.md` — 1.9-inch landscape face selection, electrical path, bandwidth, alternatives, and qualification.
- `mechanical-envelope.md` — volume, layout, tolerances, and serviceability.
- `power-and-thermal.md` — power tree, measurements, battery, charging, and heat.
- `pin-and-bus-plan.md` — provisional interfaces and conflict-resolution process.
- `sources.md` — authoritative vendor references and claims used by this plan.

Every received module gets a hardware ID, exact SKU/revision, dimensions, mass, connector orientation, logic levels, idle/active/peak current, thermal notes, driver status, calibration needs, and a photograph/scan before integration.
