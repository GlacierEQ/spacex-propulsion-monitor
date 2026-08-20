# Multi-Sensor Equipment Health Laboratory

> **Installable, deterministic local health scoring, anomaly evaluation, simulated state transitions, trend/correlation diagnostics, degradation fits, and vibration spectra for synthetic or caller-supplied local telemetry.**

This is an independent GlacierEQ portfolio repository. It is **not affiliated with, endorsed by, or connected to SpaceX** and has no access to Raptor, Merlin, Falcon, Starship, test-stand, flight, or proprietary engine telemetry or command systems.

Evidence state: `LOCAL_PROPULSION_HEALTH_SIMULATION_NOT_FLIGHT_ENGINE_AUTHORITY`

## What the software does

The repository is a local software laboratory, not an engine-control system:

- bounded health-index arithmetic for synthetic pressure-ratio, mixture-error, and vibration samples;
- per-unit multi-sensor rolling windows, means, variance, rate-of-change, threshold checks, and outlier detection;
- independent health state per simulated unit so one unit's anomaly cannot contaminate unrelated units;
- fail-closed finite, non-negative, and monotonic sample validation;
- isolated anomaly/shutdown observers so callback failures do not corrupt the state machine;
- in-memory simulated startup, throttle-profile, shutdown, and emergency-stop state transitions with no external side effects;
- linear threshold-crossing projection, exact-timestamp cross-sensor correlation, simple degradation-curve fitting, and dependency-free vibration spectra;
- diagnostic scores and projected threshold horizons explicitly labeled as **heuristics, not calibrated failure probability, diagnosis, or remaining useful life**.

Historical class/file names such as `RaptorHealthMonitor`, `EngineController`, and `FailurePrediction` remain for source compatibility. Those names do not establish Raptor data, hardware control, flight authority, or validated failure prediction.

## Install and execute

```bash
python -m pip install .
health-lab-demo
```

The installed command exercises scalar health scoring, per-unit anomaly detection, simulated local state transitions, trend projection, and spectral analysis and emits a deterministic SHA-256 receipt with `external_actions_executed: 0`.

Repository verification:

```bash
bash scripts/ci/verify.sh
```

That gate compiles source, runs deterministic/adversarial tests, builds and installs a wheel, executes the installed CLI, executes the selected direct operator, verifies the public truth boundary, and enforces the active machine contracts.

## Core implementation

| Path | Verified role |
|---|---|
| `src/prop_health.py` | Bounded local health-index arithmetic |
| `src/alpha/raptor_health.py` | Generic per-unit rolling sensor/anomaly evaluator; historical class alias retained |
| `src/omega/engine_controller.py` | In-memory simulated multi-unit state coordinator |
| `src/omega/predictive_health.py` | Heuristic trend/correlation/degradation/spectral diagnostics |
| `src/health_lab_cli.py` | Installed deterministic product/demo surface |
| `scripts/operate.py` | Direct repository operability probe |
| `tests/` | Deterministic and adversarial local proof |
| `scripts/verify_public_surface.py` | Fail-closed public/machine truth verifier |
| `machine/capability-planes.json` | APEX capability selections, challengers, donors, target frontier, evidence, and lineage |
| `machine/crystallization/` | Purpose, capability, execution, gap, and completion evidence |

## APEX evolution

Current implementations are selected per capability and remain challengeable. Predictive-health research, controller mechanisms, anomaly work, service integration, and alarm-policy work remain visible as challengers, donors, or target-frontier items rather than being discarded because they exceed today's public proof ceiling.

## Evidence boundary

This repository does **not** claim SpaceX affiliation, proprietary or flight telemetry, engine-specific specification authority, calibrated failure probability, validated remaining useful life, certified diagnosis, real throttle/shutdown/abort authority, **flight-computer command authority**, production deployment, flight readiness, safety certification, or production-scale performance.

Any future claim above this ceiling requires new source, calibrated or independent evidence where applicable, deterministic tests, exact-head receipts, and successful APEX capability-graph re-evaluation for the relevant capability.
