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
    excellence = json.loads(read("machine/excellence-state.json"))

    for surface in (readme, health_index, monitor, predictive):
        assert TOKEN in surface
    assert "from alpha.raptor_health import (" in controller
    assert "EVIDENCE_STATE," in controller

    assert "not affiliated with, endorsed by, or connected to SpaceX" in readme
    assert "Historical class/file names" in readme
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
    assert target["evidence_token"] == TOKEN
    assert target["current"]["deployed"] is False
    assert target["verified_capability"] == (
        "deterministic-local-multi-sensor-health-evaluation"
    )
    assert excellence["principal_state"] == "TESTED"
    assert excellence["evidence_token"] == TOKEN
    assert "HYPER_VALIDATED" not in json.dumps(excellence, sort_keys=True)

    print(TOKEN)


if __name__ == "__main__":
    main()
