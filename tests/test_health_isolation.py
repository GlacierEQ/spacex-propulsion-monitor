from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alpha.raptor_health import (
    EVIDENCE_STATE,
    HealthState,
    RaptorHealthMonitor,
    SensorKind,
    SensorReading,
    SensorWindow,
)
from omega.engine_controller import EngineController, EngineMode, ThrottleProfile
from omega.predictive_health import (
    CrossSensorCorrelator,
    PredictiveHealthMonitor,
    SensorTimeSeries,
    TrendExtrapolator,
    VibrationSpectralAnalyzer,
)
from prop_health import Sample, health


def test_bad_prop_health_samples_fail_closed_and_floor_is_removed() -> None:
    with pytest.raises(ValueError):
        health(Sample(math.nan, 0.0, 1.0))
    with pytest.raises(ValueError):
        health(Sample(1.0, -0.1, 1.0))

    result = health(Sample(0.0, 1.0, 100.0))
    assert result["status"] == "RED"
    assert result["health"] == 0.0
    assert result["evidence_state"] == EVIDENCE_STATE


def test_sensor_window_rejects_non_monotonic_and_nonfinite_samples() -> None:
    window = SensorWindow(5)
    window.push(1.0, 10.0)
    with pytest.raises(ValueError):
        window.push(2.0, 9.0)
    with pytest.raises(ValueError):
        window.push(math.inf, 11.0)


def test_health_state_is_isolated_per_simulated_unit() -> None:
    monitor = RaptorHealthMonitor()
    for index in range(5):
        monitor.ingest(
            SensorReading(
                SensorKind.CHAMBER_PRESSURE,
                300.0,
                float(index),
                engine_id=1,
            )
        )

    monitor.ingest(
        SensorReading(
            SensorKind.CHAMBER_PRESSURE,
            100.0,
            10.0,
            engine_id=0,
        )
    )

    assert monitor.state_for(0) == HealthState.DEGRADED
    assert monitor.state_for(1) == HealthState.NOMINAL
    assert monitor.get_engine_health(0)["state"] == "DEGRADED"
    assert monitor.get_engine_health(1)["state"] == "NOMINAL"
    assert monitor.get_engine_health(1)["evidence_state"] == EVIDENCE_STATE


def test_health_recovers_after_transient_anomaly_leaves_recent_window() -> None:
    monitor = RaptorHealthMonitor()
    monitor.ingest(
        SensorReading(
            SensorKind.CHAMBER_PRESSURE,
            100.0,
            0.0,
            engine_id=0,
        )
    )
    assert monitor.state_for(0) == HealthState.DEGRADED

    for index in range(1, 11):
        monitor.ingest(
            SensorReading(
                SensorKind.CHAMBER_PRESSURE,
                300.0,
                float(index),
                engine_id=0,
            )
        )
    assert monitor.state_for(0) == HealthState.NOMINAL


def test_engine_id_rejects_boolean_string_and_negative_aliases() -> None:
    monitor = RaptorHealthMonitor()
    for invalid in (True, False, "0", -1):
        with pytest.raises(ValueError):
            SensorReading(SensorKind.VIBRATION, 1.0, 1.0, engine_id=invalid).validate()
        with pytest.raises(ValueError):
            monitor.state_for(invalid)
        with pytest.raises(ValueError):
            monitor.get_engine_health(invalid)

    controller = EngineController(2)
    controller.start_engines()
    for invalid in (True, False, "0"):
        with pytest.raises(ValueError):
            controller.process_telemetry(invalid, SensorKind.VIBRATION, 1.0)


def test_anomaly_observer_failure_is_isolated() -> None:
    monitor = RaptorHealthMonitor()

    def broken_callback(_: object) -> None:
        raise RuntimeError("observer detail")

    monitor.on_anomaly(broken_callback)
    anomaly = monitor.ingest(
        SensorReading(
            SensorKind.CHAMBER_PRESSURE,
            100.0,
            1.0,
            engine_id=0,
        )
    )
    assert anomaly is not None
    assert monitor.state_for(0) == HealthState.DEGRADED
    assert monitor.callback_failures == 1


def test_controller_state_transitions_are_local_and_callback_safe() -> None:
    controller = EngineController(2)
    started = controller.start_engines()
    assert started["action"] == "SIMULATED_STARTUP"
    assert started["evidence_state"] == EVIDENCE_STATE

    def broken_shutdown_callback(_: dict) -> None:
        raise RuntimeError("observer detail")

    controller.on_shutdown(broken_shutdown_callback)
    assert controller.shutdown_engine(0, "fixture") is True
    assert controller._engines[0].mode == EngineMode.SHUTDOWN
    assert controller.callback_failures == 1
    assert "fixture" not in str(controller.event_log)

    stopped = controller.emergency_stop("fixture stop")
    assert stopped["action"] == "SIMULATED_EMERGENCY_STOP"
    assert stopped["evidence_state"] == EVIDENCE_STATE
    assert controller._engines[1].mode == EngineMode.EMERGENCY_STOP


def test_profile_application_uses_direct_throttle_mode_transitions() -> None:
    controller = EngineController(1)
    controller.start_engines()
    controller.add_profile(ThrottleProfile("fixture", [(0.0, 30.0), (10.0, 60.0)]))

    low = controller.apply_profile("fixture", 0.0)
    assert low["throttle"] == 30.0
    assert controller._engines[0].mode == EngineMode.THROTTLE_DOWN

    nominal = controller.apply_profile("fixture", 10.0)
    assert nominal["throttle"] == 60.0
    assert controller._engines[0].mode == EngineMode.NOMINAL


def test_controller_rejects_bad_throttle_and_unknown_unit() -> None:
    controller = EngineController(1)
    controller.start_engines()
    with pytest.raises(ValueError):
        controller.set_throttle(0, math.nan)
    with pytest.raises(ValueError):
        controller.set_throttle(0, 101.0)
    with pytest.raises(ValueError):
        controller.process_telemetry(9, SensorKind.VIBRATION, 1.0)


def test_controller_default_timestamp_matches_wall_clock_domain() -> None:
    controller = EngineController(1)
    controller.start_engines()
    explicit = time.time()
    controller.process_telemetry(
        0,
        SensorKind.VIBRATION,
        1.0,
        timestamp=explicit,
    )
    controller.process_telemetry(0, SensorKind.VIBRATION, 1.1)
    health_state = controller.health_monitor.get_engine_health(0)
    assert health_state["sensors"]["VIBRATION"]["samples"] == 2


def test_throttle_profile_rejects_unordered_or_out_of_range_points() -> None:
    with pytest.raises(ValueError):
        ThrottleProfile("bad", [(10.0, 50.0), (5.0, 60.0)]).validate()
    with pytest.raises(ValueError):
        ThrottleProfile("bad", [(0.0, 110.0)]).validate()


def test_trend_projection_score_is_bounded_heuristic_not_probability() -> None:
    series = SensorTimeSeries("fixture", 0)
    for index in range(20):
        series.append(float(index), float(index))
    result = TrendExtrapolator().extrapolate_to_threshold(series, 25.0, "above")
    assert result is not None
    assert result["time_to_threshold_s"] > 0
    assert 0.0 <= result["confidence"] <= 0.95
    assert result["score_semantics"] == "heuristic_fit_not_probability"
    assert result["evidence_state"] == EVIDENCE_STATE


def test_active_threshold_violation_emits_immediate_local_diagnostic() -> None:
    monitor = PredictiveHealthMonitor()
    warnings = monitor.ingest_sensor_data(0, "chamber_pressure", 400.0, 1.0)
    assert len(warnings) == 1
    warning = warnings[0]
    assert warning.failure_mode == "CHAMBER_PRESSURE_OVERLIMIT_ACTIVE"
    assert warning.predicted_time_s == 0.0
    assert warning.confidence == 1.0
    assert "not probability" in warning.evidence[-1]


def test_negative_correlation_remains_bounded_and_diagnostic_only() -> None:
    left = SensorTimeSeries("left", 0)
    right = SensorTimeSeries("right", 0)
    for index in range(20):
        left.append(float(index), float(index))
        right.append(float(20 - index), float(index))

    correlator = CrossSensorCorrelator(correlation_threshold=0.5)
    correlator.register_sensor("left", left)
    correlator.register_sensor("right", right)
    correlation = correlator.compute_correlation("left", "right")
    assert correlation is not None
    assert -1.0 <= correlation <= 1.0
    assert correlation < 0


def test_vibration_spectrum_is_local_math_not_fault_diagnosis() -> None:
    analyzer = VibrationSpectralAnalyzer(sampling_rate_hz=1000.0)
    data = [math.sin(2 * math.pi * 50 * index / 1000.0) for index in range(256)]
    spectrum = analyzer.compute_spectrum(data)
    assert spectrum["evidence_state"] == EVIDENCE_STATE
    assert spectrum["dominant_frequency"] >= 0
    signature = analyzer.classify_fault(spectrum)
    if signature is not None:
        assert signature["score_semantics"] == "heuristic_not_probability_or_diagnosis"
