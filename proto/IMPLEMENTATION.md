# Schema Implementation Plan

## Phase 0 decision spike

Compare Protobuf with lite runtime, FlatBuffers or a deliberately small alternative against C++17 ARM target, Python/Jarvis tooling, controller constraints, code size/RAM, backward compatibility, fuzzability and diagnostics. The high-level contracts in `docs/architecture/contracts.md` are fixed; wire technology is an ADR.

The controller link may use a separate compact schema/framing from network/world messages, but shares generated enums/units where safe. Do not force a large runtime onto the MCU.

## Repository layout

- `schema/`: canonical definitions by domain and major version.
- `generated/`: build-generated or release snapshot according to language/tooling decision; never hand-edited.
- `fixtures/`: golden bytes plus human-readable semantic representation.
- `validation/`: cross-field/range rules not expressible in schema.
- `compat/`: current and supported prior-version reader/writer matrices.
- `docs/`: generated field/unit/compatibility reference.

## Design rules

- Names include units or refer to a documented unit type.
- IDs distinguish device/session/action/event/observation/track.
- Time fields identify clock domain; durations/TTL are explicit.
- Optionality is intentional. Missing safety-relevant values never default to permissive behavior.
- Enums reserve zero as unspecified/invalid and readers handle unknown values.
- Floating values define finite/range rules; fixed-point considered for controller.
- Streaming payloads have maximum sizes/rates and chunking policy.
- Sensitive fields carry privacy classification where useful.
- Every schema version has compatibility and migration notes.

## Evolution workflow

Propose semantic change with producer/consumer list and compatibility impact; land schema + validation + golden current/prior fixtures; regenerate all languages; update adapters and contract docs; run compatibility matrix; then land producers before enabling new behavior. Major breaks require explicit negotiation/migration and ADR.

## Milestones

- PR0: wire-format ADR and toolchain.
- PR1: common/event/action/expression/Jarvis v0.
- PR2: health/config/replay/storage identities.
- PR3: observation/track/pose/world schemas.
- PR4: controller v1 protocol and golden C++/MCU fixtures.
- PR5: release compatibility automation and generated reference.

