#!/usr/bin/env python3
"""Execute the selected local health-lab capability and emit a deterministic receipt."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from health_lab_cli import build_demo_receipt  # noqa: E402


def _stable(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_receipt() -> dict:
    demo = build_demo_receipt()
    body = {
        "schema": "glaciereq.health-operate-receipt.v1",
        "selection_mode": "CURRENT_BEST_REVISABLE",
        "capability": "deterministic-local-multi-sensor-health-evaluation",
        "evidence_state": demo["evidence_state"],
        "demo": demo,
        "external_actions_executed": demo["external_actions_executed"],
    }
    return {**body, "receipt_sha256": hashlib.sha256(_stable(body)).hexdigest()}


def main() -> int:
    receipt = build_receipt()
    demo = receipt["demo"]
    print(json.dumps(receipt, indent=2, sort_keys=True))
    valid = (
        receipt["selection_mode"] == "CURRENT_BEST_REVISABLE"
        and receipt["capability"] == "deterministic-local-multi-sensor-health-evaluation"
        and receipt["evidence_state"] == "LOCAL_PROPULSION_HEALTH_SIMULATION_NOT_FLIGHT_ENGINE_AUTHORITY"
        and demo["scalar_health"]["status"] == "GREEN"
        and demo["multi_sensor"]["anomaly"] is not None
        and demo["simulated_control"]["startup"] == "SIMULATED_STARTUP"
        and demo["simulated_control"]["emergency_action"] == "SIMULATED_EMERGENCY_STOP"
        and demo["diagnostics"]["trend"] is not None
        and len(demo["digest"]) == 64
        and receipt["external_actions_executed"] == 0
        and len(receipt["receipt_sha256"]) == 64
    )
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
