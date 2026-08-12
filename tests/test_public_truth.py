from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "LOCAL_PROPULSION_HEALTH_SIMULATION_NOT_FLIGHT_ENGINE_AUTHORITY"
APPROVED_CAPABILITIES = [
    "bounded-synthetic-health-indexing",
    "per-unit-multi-sensor-windowing",
    "threshold-and-outlier-detection",
    "local-state-transition-simulation",
    "heuristic-threshold-trend-projection",
    "cross-sensor-correlation",
    "simple-degradation-curve-fitting",
    "dependency-free-vibration-spectrum-analysis",
    "local-python-verification",
    "installable-local-library-and-cli",
    "direct-operability-and-public-truth-verification",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_public_surface_is_explicitly_non_affiliated_and_local_only() -> None:
    readme = read("README.md")
    assert TOKEN in readme
    assert "not affiliated with, endorsed by, or connected to SpaceX" in readme
    assert "Historical class/file names" in readme
    assert "Real-time Raptor/Merlin" not in readme
    assert "100+ engine telemetry" not in readme
    assert "LSTM anomaly detector trained on 1000+" not in readme
    assert "engine_health(engine_id)" not in readme
    assert "flight-computer command authority" in readme


def test_predictive_source_cannot_claim_validated_raptor_failure_prediction() -> None:
    predictive = read("src/omega/predictive_health.py")
    assert TOKEN in predictive
    assert "Predicts Raptor engine failure 30-120 seconds" not in predictive
    assert "redistribute thrust or initiate safe abort" not in predictive
    assert "heuristic_not_probability_or_diagnosis" in predictive
    assert "illustrative_threshold_horizon_not_rul" in predictive


def test_controller_source_is_in_memory_simulation_only() -> None:
    controller = read("src/omega/engine_controller.py")
    assert "from alpha.raptor_health import (" in controller
    assert "EVIDENCE_STATE," in controller
    assert "no external side effects" in controller
    assert "SIMULATED_STARTUP" in controller
    assert "SIMULATED_EMERGENCY_STOP" in controller


def test_machine_truth_matches_current_scope() -> None:
    capabilities = json.loads(read("machine/capabilities.json"))
    target = json.loads(read("machine/target-contract.json"))
    excellence = json.loads(read("machine/excellence-state.json"))
    assert capabilities["capabilities"] == APPROVED_CAPABILITIES
    assert capabilities["evidence_token"] == TOKEN
    assert target["evidence_token"] == TOKEN
    assert target["verified_capability"] == (
        "deterministic-local-multi-sensor-health-evaluation"
    )
    assert target["current"]["deployed"] is False
    assert excellence["principal_state"] == "TESTED"
    assert excellence["evidence_token"] == TOKEN
    assert "HYPER_VALIDATED" not in json.dumps(excellence, sort_keys=True)
