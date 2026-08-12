#!/usr/bin/env python3
"""Execute the canonical local health-lab product surface directly."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from health_lab_cli import build_demo_receipt  # noqa: E402


def main() -> int:
    receipt = build_demo_receipt()
    print(json.dumps(receipt, indent=2, sort_keys=True))
    required = (
        receipt["evidence_state"]
        == "LOCAL_PROPULSION_HEALTH_SIMULATION_NOT_FLIGHT_ENGINE_AUTHORITY"
        and receipt["scalar_health"]["status"] == "GREEN"
        and receipt["multi_sensor"]["anomaly"] is not None
        and receipt["simulated_control"]["startup"] == "SIMULATED_STARTUP"
        and receipt["simulated_control"]["emergency_action"] == "SIMULATED_EMERGENCY_STOP"
        and receipt["diagnostics"]["trend"] is not None
        and len(receipt["digest"]) == 64
        and receipt["external_actions_executed"] == 0
    )
    return 0 if required else 2


if __name__ == "__main__":
    raise SystemExit(main())
