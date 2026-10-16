# Simulation and Scenario Laboratory

## Scope

`simulation/` provides deterministic virtual time, world/robot/sensor/actuator/network models, Jarvis events, fault injection, scenario manifests, trace/replay, assertion framework, visualization adapters, and accelerated-day/endurance runs.

Simulation is a development and regression environment, not proof that physical hardware is safe. Model parameters are versioned and compared to measurements; mismatch is visible.

## Design target

Most high-level code runs unchanged against simulated interfaces. A scenario is executable documentation containing initial world/state, hardware/profile assumptions, seed, timed events, expected invariants/outcomes, and artifacts.

