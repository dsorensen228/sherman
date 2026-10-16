# Mechanical Design and CAD

## Scope

`cad/` owns measured component models, robot assembly, parametric envelope/layout studies, chassis/shell/mounts, optical windows/baffles, harness retention, drawings, print/manufacturing profiles, mass/center-of-mass estimate, tolerance stack, assembly and inspection artifacts.

It does not define electrical ratings, firmware pin assignments, sensor algorithms or safety thresholds alone. Mechanical choices that affect FOV, cliff margin, antenna, heat, wheel geometry, battery or service control require the relevant owner/ADR.

## Source-of-truth policy

Vendor STEP files are references; verify against the received part. Simple parts may be modeled from caliper/scan dimensions with confidence. Generated meshes/exports are derived from editable parametric sources and never hand-edited.

## Component model inventory

`components/` maps every carried shopping-list line to its manufacturer CAD
source, records checksums and fit limitations, and provides a reproducible
fetcher for the ignored vendor-model cache. Start with
`components/README.md` before assembling the first volume model.
