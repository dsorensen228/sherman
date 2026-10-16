# Navigation and Localization

## Scope

`navigation/` owns frame graph, odometry consumption, localization/fusion, map-facing pose, traversability/occupancy representation, footprint/inflation, goal/path/trajectory planning, motion-control proposals, progress/stuck detection, bounded recovery, and v1 docking navigation.

It never directly writes motor GPIO or controller frames. Output is a motion proposal with expiry, limits, action ID and explanation; core safety and the controller may limit or reject it.

## Safety boundary

Cliff reflexes remain controller-owned and do not depend on a map. Navigation uses map/pose/edge evidence to avoid approaching hazards, but mapping failure must make motion more conservative rather than disable hardware stop.
