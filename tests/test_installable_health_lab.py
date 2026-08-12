from __future__ import annotations

import json
import subprocess
import sys

from health_lab_cli import build_demo_receipt


def test_demo_receipt_exercises_real_health_lab() -> None:
    receipt = build_demo_receipt()
    assert receipt["evidence_state"] == "LOCAL_PROPULSION_HEALTH_SIMULATION_NOT_FLIGHT_ENGINE_AUTHORITY"
    assert receipt["scalar_health"]["status"] == "GREEN"
    assert receipt["multi_sensor"]["anomaly"]["severity"] == "CRITICAL"
    assert receipt["simulated_control"]["startup"] == "SIMULATED_STARTUP"
    assert receipt["simulated_control"]["critical_sample"]["severity"] == "CRITICAL"
    assert receipt["simulated_control"]["emergency_action"] == "SIMULATED_EMERGENCY_STOP"
    assert receipt["diagnostics"]["trend"]["score_semantics"] == "heuristic_fit_not_probability"
    assert receipt["external_actions_executed"] == 0
    assert len(receipt["digest"]) == 64


def test_operate_script_emits_same_bounded_product_surface() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/operate.py"],
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(result.stdout)
    assert receipt["multi_sensor"]["anomaly"]["sensor"] == "VIBRATION"
    assert receipt["external_actions_executed"] == 0
