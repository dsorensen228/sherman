# Evidence Artifacts

Implementation and test runs place reviewable evidence under `artifacts/<phase>/<packet-id>/`. Large/generated/private files may be excluded from version control but must be referenced by a manifest with checksum, retention and access location.

Each packet directory includes `RESULTS.md`, build/config/hardware/calibration identities, exact commands/protocol, machine-readable test output, relevant logs/metrics/plots/media and deviations/residual risks. Never store credentials or ungoverned private camera data here.

