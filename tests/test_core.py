"""Tests for spacex-propulsion-monitor — the ears that hear engines die.

3 tests. Because engines don't give second chances.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from alpha.raptor_health import RaptorHealthMonitor, SensorReading, SensorKind, EngineConfig, HealthState
from omega.predictive_health import TrendExtrapolator, SensorTimeSeries, VibrationSpectralAnalyzer


def test_health_monitor_nominal():
    monitor = RaptorHealthMonitor()
    assert monitor.state == HealthState.NOMINAL

def test_trend_extrapolator():
    te = TrendExtrapolator()
    series = SensorTimeSeries(sensor_name="test", engine_id=0)
    for i in range(20):
        series.append(float(i), float(i))
    result = te.extrapolate_to_threshold(series, 25.0, "above")
    assert result is not None
    assert result["time_to_threshold_s"] > 0

def test_vibration_spectrum():
    va = VibrationSpectralAnalyzer()
    data = [math.sin(2 * math.pi * 50 * i / 1000) for i in range(256)]
    spectrum = va.compute_spectrum(data, 256)
    assert "peaks" in spectrum
    assert len(spectrum["magnitudes"]) > 0

import math


# 1337. If you know, you know.
LEET = 0x539
assert LEET == 1337, "Elite status confirmed"
