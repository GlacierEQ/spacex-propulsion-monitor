"""Propulsion monitor tests."""

import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from alpha.raptor_health import (
    RaptorHealthMonitor, SensorReading, SensorKind, HealthState, EngineConfig,
)
from omega.engine_controller import (
    EngineController, ThrottleProfile, EngineMode,
)


def test_sensor_window():
    from alpha.raptor_health import SensorWindow
    w = SensorWindow(5)
    for i in range(10):
        w.push(float(i), time.time())
    assert len(w._values) == 5
    assert w.mean == 7.0


def test_health_monitor_nominal():
    monitor = RaptorHealthMonitor()
    for i in range(10):
        r = SensorReading(SensorKind.CHAMBER_PRESSURE, 300.0, time.time(), 0)
        monitor.ingest(r)
    assert monitor.state == HealthState.NOMINAL


def test_health_monitor_anomaly():
    monitor = RaptorHealthMonitor()
    for i in range(5):
        r = SensorReading(SensorKind.CHAMBER_PRESSURE, 300.0, time.time(), 0)
        monitor.ingest(r)

    bad = SensorReading(SensorKind.CHAMBER_PRESSURE, 100.0, time.time(), 0)
    anomaly = monitor.ingest(bad)
    assert anomaly is not None
    assert anomaly.severity == "CRITICAL"


def test_health_monitor_callback():
    monitor = RaptorHealthMonitor()
    anomalies = []
    monitor.on_anomaly(lambda a: anomalies.append(a))

    for i in range(5):
        r = SensorReading(SensorKind.CHAMBER_PRESSURE, 300.0, time.time(), 0)
        monitor.ingest(r)

    bad = SensorReading(SensorKind.CHAMBER_PRESSURE, 400.0, time.time(), 0)
    monitor.ingest(bad)
    assert len(anomalies) == 1


def test_engine_controller_startup():
    ec = EngineController(9)
    result = ec.start_engines()
    assert result["engines"] == 9
    for eid in range(9):
        assert ec._engines[eid].mode == EngineMode.STARTUP


def test_throttle():
    ec = EngineController(9)
    ec.start_engines()
    ec.set_throttle(0, 80)
    assert ec._engines[0].throttle_percent == 80
    assert ec._engines[0].mode == EngineMode.NOMINAL


def test_shutdown():
    ec = EngineController(9)
    ec.start_engines()

    shutdowns = []
    ec.on_shutdown(lambda e: shutdowns.append(e))

    ec.shutdown_engine(0, "test")
    assert ec._engines[0].mode == EngineMode.SHUTDOWN
    assert len(shutdowns) == 1


def test_emergency_stop():
    ec = EngineController(9)
    ec.start_engines()
    result = ec.emergency_stop("manual test")
    assert len(result["stopped"]) == 9
    for eid in range(9):
        assert ec._engines[eid].mode == EngineMode.EMERGENCY_STOP


def test_throttle_profile():
    profile = ThrottleProfile("standard", [
        (0, 100), (10, 80), (60, 60), (180, 100),
    ])
    assert profile.get_throttle(0) == 100
    assert profile.get_throttle(5) == 90
    assert profile.get_throttle(180) == 100


def test_vehicle_status():
    ec = EngineController(9)
    ec.start_engines()
    status = ec.get_vehicle_status()
    assert status["engines_active"] == 9
    assert status["engines_total"] == 9


def test_telemetry_critical_triggers_shutdown():
    ec = EngineController(9)
    ec.start_engines()

    for i in range(5):
        ec.process_telemetry(0, SensorKind.CHAMBER_PRESSURE, 300.0)

    ec.process_telemetry(0, SensorKind.CHAMBER_PRESSURE, 100.0)
    assert ec._engines[0].mode == EngineMode.SHUTDOWN


def test_engine_out_degradation():
    ec = EngineController(9)
    ec.start_engines()
    ec.shutdown_engine(4, "engine out")
    status = ec.get_vehicle_status()
    assert status["engines_active"] == 8


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
