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


def load(path: str) -> dict:
    return json.loads(read(path))


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


def test_machine_projection_matches_current_evidence_without_erasing_target() -> None:
    capabilities = load("machine/capabilities.json")
    target = load("machine/target-contract.json")
    planes = load("machine/capability-planes.json")
    excellence = load("machine/excellence-state.json")

    assert capabilities["capabilities"] == APPROVED_CAPABILITIES
    assert capabilities["evidence_token"] == TOKEN

    evidence = target["evidence_checkpoint"]
    assert evidence["evidence_token"] == TOKEN
    assert evidence["verified_capability"] == (
        "deterministic-local-multi-sensor-health-evaluation"
    )
    assert target["implementation_checkpoint"]["deployed"] is False
    assert target["target_architecture"]["status"] == (
        "PRESERVED_UNVERIFIED_TARGET_ARCHITECTURE"
    )
    assert len(target["target_architecture"]["objectives"]) >= 7

    assert planes["projection"]["public_claim_ceiling"].startswith("local synthetic")
    assert planes["target"]["status"] == "PRESERVED_UNVERIFIED_TARGET_ARCHITECTURE"
    target_states = {item["state"] for item in planes["target"]["items"]}
    assert "UNVERIFIED_TARGET" in target_states
    assert "PARTIALLY_IMPLEMENTED_TARGET" in target_states
    assert planes["projection"]["projection_may_overwrite_canonical_or_target"] is False

    assert excellence["product_state"] == "FUNCTIONAL_CRYSTALLIZATION_CANDIDATE"
    assert excellence["evidence_state"] == "EXACT_HEAD_VERIFIED"
    assert excellence["projection_state"] == TOKEN
    assert excellence["target_state"] == "PRESERVED_UNVERIFIED_TARGET_ARCHITECTURE"
    assert excellence["evidence_checkpoint"]["head_sha"] == (
        "878283ace1aae2807ea8179b37aa8c1319f48cdd"
    )
    assert "HYPER_VALIDATED" not in json.dumps(excellence, sort_keys=True)


def test_historical_ambition_is_preserved_only_as_target_not_public_fact() -> None:
    planes = load("machine/capability-planes.json")
    readme = read("README.md")
    targets = {item["capability"]: item for item in planes["target"]["items"]}
    assert "high-channel-count multi-parameter monitoring" in targets
    assert targets["high-channel-count multi-parameter monitoring"]["state"] == (
        "UNVERIFIED_TARGET"
    )
    assert "MCP-queryable equipment-health service" in targets
    assert targets["MCP-queryable equipment-health service"]["state"] == "UNVERIFIED_TARGET"
    assert "100+ engine telemetry" not in readme
    assert "engine_health(engine_id)" not in readme
