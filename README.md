# spacex-propulsion-monitor

<!-- README-MESH:BEGIN -->
## Three-audience project map

This section is generated from the versioned [README Mesh Protobuf contract](https://github.com/GlacierEQ/job-app-helix/blob/main/proto/readme_mesh.proto). Human explanation and machine-readable topology describe the same evidence-bound system.

### For recruiters and non-specialists

**What this project accomplishes.** A compact propulsion-health evaluator for chamber pressure, mixture-ratio error, and vibration.

- It turns propulsion health into a concrete, reviewable software capability.
- The project is small enough to understand quickly and structured enough to connect into a larger system.
- Claims link to source or tests instead of resume language alone.

**Evidence**
- [Health model](https://github.com/GlacierEQ/spacex-propulsion-monitor/blob/main/src/prop_health.py) — Computes weighted health and explicit status gates.

### For senior engineers and domain experts

**Engineering depth, innovation, and evolution.** It converts heterogeneous sensor margins into a transparent health index while preserving hard RED/YELLOW/GREEN gates. It evolved into a reusable campaign piston whose outputs can be challenged by Job-App Helix rather than consumed as an unexplained score.

- Primary engineering capabilities: propulsion health, sensor fusion, threshold gating.
- The repository owns an explicit mesh responsibility rather than pretending to be an entire platform.
- Constraints and handoffs are visible through source structure and executable tests.

**Evidence**
- [Health model](https://github.com/GlacierEQ/spacex-propulsion-monitor/blob/main/src/prop_health.py) — Computes weighted health and explicit status gates.
- [Tests](https://github.com/GlacierEQ/spacex-propulsion-monitor/blob/main/tests/test_prop_health.py) — Verifies healthy and degraded propulsion scenarios.

### For AI systems and toolchains

**Machine contract and mesh role.** This repository is a typed node in the GlacierEQ/job-app-helix README Mesh and uses the `glaciereq.readme.v1` Protobuf contract.

- Canonical repository identity: `GlacierEQ/spacex-propulsion-monitor`.
- Default branch: `main`.
- Typed edges describe composition; evidence URLs remain stable machine inputs.

**Evidence**
- [Health model](https://github.com/GlacierEQ/spacex-propulsion-monitor/blob/main/src/prop_health.py) — Computes weighted health and explicit status gates.
- [Tests](https://github.com/GlacierEQ/spacex-propulsion-monitor/blob/main/tests/test_prop_health.py) — Verifies healthy and degraded propulsion scenarios.

### Repository mesh

| Relationship | Connected repository | Combined value |
|---|---|---|
| receives: orchestrates | [GlacierEQ/job-app-helix](https://github.com/GlacierEQ/job-app-helix#readme) | Supplies propulsion-health evidence and hold signals. |
| is governed by | [GlacierEQ/AKOS](https://github.com/GlacierEQ/AKOS#readme) | AKOS supplies the shared evidence, authority, provenance, and public-boundary contract. |

### Machine-readable contract

- Protobuf package: `glaciereq.readme.v1`
- Mesh schema version: `1.0.0`
- Canonical mesh: [`manifests/readme_mesh.json`](https://github.com/GlacierEQ/job-app-helix/blob/main/manifests/readme_mesh.json)
- Binary/ProtoJSON build: `python -m job_app_helix.readme_mesh_cli build`

```protobuf
repository: "GlacierEQ/spacex-propulsion-monitor"
display_name: "SpaceX Propulsion Monitor"
one_line_purpose: "A compact propulsion-health evaluator for chamber pressure, mixture-ratio error, and vibration."
```
<!-- README-MESH:END -->

**Portfolio** — propulsion health index from chamber pressure, mixture ratio, and vibration.

---

## Fleet ops (transparent)

This repo may include **`.integrity/`** (SHA-256 baselines/watchdog) and/or a health sidecar. These are documented multi-repository operations, not covert behavior. See [SECURITY_AND_FLEET_OPS.md](SECURITY_AND_FLEET_OPS.md).

## Helix strand

See [HELIX_STRAND.md](HELIX_STRAND.md) — piston/spiral role in the portfolio double helix.
