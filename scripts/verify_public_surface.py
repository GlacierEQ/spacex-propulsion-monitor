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


def main() -> None:
    readme = read("README.md")
    health_index = read("src/prop_health.py")
    monitor = read("src/alpha/raptor_health.py")
    controller = read("src/omega/engine_controller.py")
    predictive = read("src/omega/predictive_health.py")
    capabilities = json.loads(read("machine/capabilities.json"))
    target = json.loads(read("machine/target-contract.json"))
    planes = json.loads(read("machine/capability-planes.json"))
    excellence = json.loads(read("machine/excellence-state.json"))
    gaps = json.loads(read("machine/crystallization/gap-matrix.json"))

    for surface in (readme, health_index, monitor, predictive):
        assert TOKEN in surface
    assert "from alpha.raptor_health import (" in controller
    assert "EVIDENCE_STATE," in controller

    assert "not affiliated with, endorsed by, or connected to SpaceX" in readme
    assert "Historical class/file names" in readme
    assert "flight-computer command authority" in readme
    assert "Real-time Raptor/Merlin" not in readme
    assert "100+ engine telemetry" not in readme
    assert "LSTM anomaly detector trained on 1000+" not in readme
    assert "engine_health(engine_id)" not in readme
    assert "Predicts Raptor engine failure 30-120 seconds" not in predictive
    assert "redistribute thrust or initiate safe abort" not in predictive
    assert "single failure probability" not in predictive
    assert "heuristic_not_probability_or_diagnosis" in predictive
    assert "illustrative_threshold_horizon_not_rul" in predictive
    assert "SIMULATED_STARTUP" in controller
    assert "SIMULATED_EMERGENCY_STOP" in controller

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

    assert planes["projection"]["projection_may_overwrite_canonical_or_target"] is False
    assert planes["target"]["status"] == "PRESERVED_UNVERIFIED_TARGET_ARCHITECTURE"
    assert len(planes["target"]["items"]) >= 7
    target_states = {item["state"] for item in planes["target"]["items"]}
    assert "UNVERIFIED_TARGET" in target_states
    assert "PARTIALLY_IMPLEMENTED_TARGET" in target_states

    assert gaps["gaps"] == []
    assert excellence["product_state"] == "FUNCTIONAL_CRYSTALLIZATION_CANDIDATE"
    assert excellence["evidence_state"] == "EXACT_HEAD_VERIFIED"
    assert excellence["projection_state"] == TOKEN
    assert excellence["target_state"] == "PRESERVED_UNVERIFIED_TARGET_ARCHITECTURE"
    assert excellence["evidence_checkpoint"]["head_sha"] == (
        "878283ace1aae2807ea8179b37aa8c1319f48cdd"
    )
    assert "HYPER_VALIDATED" not in json.dumps(excellence, sort_keys=True)

    print(TOKEN)


if __name__ == "__main__":
    main()
