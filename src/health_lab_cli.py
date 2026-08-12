"""Deterministic executable surface for the local equipment-health laboratory."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from typing import Any

from alpha.raptor_health import EVIDENCE_STATE, EquipmentHealthMonitor, SensorKind, SensorReading
from omega.engine_controller import EngineController
from omega.predictive_health import SensorTimeSeries, TrendExtrapolator, VibrationSpectralAnalyzer
from prop_health import Sample, health


def _digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_demo_receipt() -> dict[str, Any]:
    """Exercise the repository's material mechanisms with deterministic local data."""
    scalar_health = health(Sample(chamber_p_pct=0.98, mr_error=0.02, vibe_g=3.0))

    monitor = EquipmentHealthMonitor()
    for index in range(5):
        monitor.ingest(
            SensorReading(
                kind=SensorKind.VIBRATION,
                value=2.0 + index * 0.05,
                timestamp=float(index),
                engine_id=0,
            )
        )
    anomaly = monitor.ingest(
        SensorReading(
            kind=SensorKind.VIBRATION,
            value=18.0,
            timestamp=5.0,
            engine_id=0,
        )
    )
    monitor_receipt = monitor.get_engine_health(0)

    controller = EngineController(engine_count=2)
    startup = controller.start_engines()
    throttle_applied = controller.set_throttle(0, 65.0)
    critical = controller.process_telemetry(
        1,
        SensorKind.VIBRATION,
        18.0,
        timestamp=1_700_000_000.0,
    )
    emergency = controller.emergency_stop("deterministic_demo")

    series = SensorTimeSeries(sensor_name="local_vibration", engine_id=0)
    for index in range(12):
        series.append(1.0 + index * 0.1, float(index))
    trend = TrendExtrapolator().extrapolate_to_threshold(series, threshold=3.0)

    wave = [math.sin(2.0 * math.pi * 2.0 * index / 32.0) for index in range(32)]
    spectrum = VibrationSpectralAnalyzer(sampling_rate_hz=32.0).compute_spectrum(wave, window_size=32)

    body = {
        "schema": "glaciereq.local-health-lab.demo.v1",
        "evidence_state": EVIDENCE_STATE,
        "scalar_health": scalar_health,
        "multi_sensor": {
            "state": monitor_receipt["state"],
            "sample_count": monitor_receipt["sensors"]["VIBRATION"]["samples"],
            "anomaly": None
            if anomaly is None
            else {
                "sensor": anomaly.sensor.name,
                "severity": anomaly.severity,
                "engine_id": anomaly.engine_id,
            },
        },
        "simulated_control": {
            "startup": startup["action"],
            "throttle_applied": throttle_applied,
            "critical_sample": critical,
            "emergency_action": emergency["action"],
            "stopped_units": emergency["stopped"],
        },
        "diagnostics": {
            "trend": trend,
            "spectrum": {
                "dominant_frequency": spectrum["dominant_frequency"],
                "total_energy": spectrum["total_energy"],
                "peak_count": len(spectrum["peaks"]),
                "evidence_state": spectrum["evidence_state"],
            },
        },
        "external_actions_executed": 0,
    }
    body["digest"] = _digest(body)
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Execute the independent local equipment-health laboratory demo"
    )
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args(argv)
    receipt = build_demo_receipt()
    print(json.dumps(receipt, sort_keys=True, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
