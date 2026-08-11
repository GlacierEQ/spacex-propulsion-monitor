# Multi-Sensor Equipment Health Laboratory

> **Deterministic local health scoring, threshold/anomaly detection, trend projection, correlation, and simulated state transitions for synthetic propulsion-like telemetry.**

This is an independent GlacierEQ portfolio repository. It is **not affiliated with, endorsed by, or connected to SpaceX** and has no access to Raptor, Merlin, Falcon, Starship, test-stand, flight, or proprietary engine telemetry or command systems.

Evidence state: `LOCAL_PROPULSION_HEALTH_SIMULATION_NOT_FLIGHT_ENGINE_AUTHORITY`

## Verified repository-owned scope

The admitted surface is a local software laboratory, not an engine-control system:

- bounded health-index arithmetic for synthetic chamber-pressure ratio, mixture-ratio error, and vibration samples;
- per-unit multi-sensor rolling windows, means, variance, rate-of-change, threshold checks, and outlier detection;
- independent health state per simulated unit so one unit's anomaly cannot contaminate unrelated units;
- fail-closed finite, non-negative, and monotonic sample validation;
- isolated anomaly/shutdown observers so callback failures do not corrupt the state machine;
- in-memory simulated startup, throttle-profile, shutdown, and emergency-stop **state transitions** with no external side effects;
- linear threshold-crossing projection, cross-sensor correlation, simple degradation-curve fitting, and dependency-free vibration spectra;
- diagnostic scores and projected threshold horizons explicitly labeled as **heuristics, not calibrated failure probability, diagnosis, or remaining useful life**;
- repository-owned deterministic tests and cold-start operability.

Historical class/file names such as `RaptorHealthMonitor`, `EngineController`, and `FailurePrediction` remain for source compatibility. Those names do not establish Raptor data, hardware control, flight authority, or validated failure prediction.

## Core implementation

| Path | Verified role |
|---|---|
| `src/prop_health.py` | Bounded local health-index arithmetic |
| `src/alpha/raptor_health.py` | Generic per-unit rolling sensor/anomaly evaluator; historical class alias retained |
| `src/omega/engine_controller.py` | In-memory simulated multi-unit state coordinator |
| `src/omega/predictive_health.py` | Heuristic trend/correlation/degradation/spectral diagnostics |
| `tests/` | Deterministic and adversarial local proof |
| `scripts/verify_public_surface.py` | Fail-closed public/machine truth verifier |

## Evidence boundary

This repository does **not** claim:

- SpaceX affiliation, endorsement, employment, or proprietary access;
- real Raptor, Merlin, Falcon, Starship, or test-stand telemetry;
- 100+ live telemetry channels, real-time engine monitoring, or production-scale throughput;
- validated engine-specific pressure, mixture-ratio, turbopump, thrust, or temperature specifications;
- calibrated failure probability, 30–120 second failure prediction, validated remaining useful life, or certified fault diagnosis;
- LSTM training on engine test-fire datasets or any proprietary training corpus;
- real throttle, shutdown, abort, thrust-redistribution, or flight-computer command authority;
- live MCP, provider, APEX, AKOS, Mastermind, or agent-mesh runtime integration;
- production deployment, flight readiness, safety certification, or operational suitability.

Any future claim above this ceiling requires new source, calibrated/independent evidence where applicable, deterministic tests, exact-head receipts, and a new governance admission.

## Reproduce the admitted surface

```bash
bash scripts/ci/verify.sh
```

The gate compiles the source, runs deterministic/adversarial tests, executes the local operability probe, and verifies the public/machine truth boundary.
