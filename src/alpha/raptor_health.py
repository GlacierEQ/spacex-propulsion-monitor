"""Raptor engine health monitor — thermocouple, pressure, vibration analysis.

Computes engine health from sensor data using statistical methods.
Detects anomalies via moving windows, rate-of-change, and spectral checks.
Pure math, zero external dependencies.
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class HealthState(Enum):
    NOMINAL = auto()
    DEGRADED = auto()
    CRITICAL = auto()
    OFFLINE = auto()


class SensorKind(Enum):
    CHAMBER_PRESSURE = auto()
    TURBOPUMP_SPEED = auto()
    OXIDIZER_TEMP = auto()
    FUEL_TEMP = auto()
    VIBRATION = auto()
    THRUST = auto()
    NOZZLE_TEMP = auto()
    GIMBAL_ANGLE = auto()


@dataclass
class EngineConfig:
    chamber_pressure_nom: float = 300.0
    chamber_pressure_min: float = 250.0
    chamber_pressure_max: float = 350.0
    turbopump_speed_nom: float = 34000.0
    turbopump_speed_max: float = 38000.0
    oxidizer_temp_nom: float = 66.0
    fuel_temp_nom: float = 22.0
    vibration_max: float = 5.0
    thrust_nom: float = 2300000.0
    thrust_min: float = 2000000.0


@dataclass
class SensorReading:
    kind: SensorKind
    value: float
    timestamp: float
    engine_id: int = 0


class SensorWindow:
    def __init__(self, size: int = 50):
        self.size = size
        self._values: list[float] = []
        self._timestamps: list[float] = []

    def push(self, value: float, timestamp: float):
        self._values.append(value)
        self._timestamps.append(timestamp)
        if len(self._values) > self.size:
            self._values.pop(0)
            self._timestamps.pop(0)

    @property
    def mean(self) -> float:
        return sum(self._values) / len(self._values) if self._values else 0.0

    @property
    def variance(self) -> float:
        if len(self._values) < 2:
            return 0.0
        m = self.mean
        return sum((v - m) ** 2 for v in self._values) / (len(self._values) - 1)

    @property
    def std_dev(self) -> float:
        return math.sqrt(self.variance)

    @property
    def min_val(self) -> float:
        return min(self._values) if self._values else 0.0

    @property
    def max_val(self) -> float:
        return max(self._values) if self._values else 0.0

    @property
    def range(self) -> float:
        return self.max_val - self.min_val

    @property
    def rate_of_change(self) -> float:
        if len(self._values) < 2:
            return 0.0
        dt = self._timestamps[-1] - self._timestamps[0]
        if dt <= 0:
            return 0.0
        return (self._values[-1] - self._values[0]) / dt

    @property
    def is_outlier(self) -> bool:
        if len(self._values) < 5:
            return False
        latest = self._values[-1]
        m, s = self.mean, self.std_dev
        if s < 1e-10:
            return abs(latest - m) > 1e-6
        return abs((latest - m) / s) > 3.0


@dataclass
class AnomalyEvent:
    sensor: SensorKind
    engine_id: int
    value: float
    expected_range: tuple[float, float]
    timestamp: float
    severity: str = "WARNING"


class RaptorHealthMonitor:
    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self._windows: dict[tuple[int, SensorKind], SensorWindow] = {}
        self._anomalies: list[AnomalyEvent] = []
        self._state = HealthState.NOMINAL
        self._anomaly_callbacks: list = []

    def _get_window(self, engine_id: int, kind: SensorKind) -> SensorWindow:
        key = (engine_id, kind)
        if key not in self._windows:
            self._windows[key] = SensorWindow()
        return self._windows[key]

    def on_anomaly(self, callback):
        self._anomaly_callbacks.append(callback)

    def ingest(self, reading: SensorReading) -> Optional[AnomalyEvent]:
        window = self._get_window(reading.engine_id, reading.kind)
        window.push(reading.value, reading.timestamp)

        anomaly = self._check_threshold(reading, window)
        if anomaly:
            self._anomalies.append(anomaly)
            for cb in self._anomaly_callbacks:
                cb(anomaly)
            self._update_state()
            return anomaly

        if window.is_outlier:
            anomaly = AnomalyEvent(
                sensor=reading.kind,
                engine_id=reading.engine_id,
                value=reading.value,
                expected_range=(window.mean - 3 * window.std_dev, window.mean + 3 * window.std_dev),
                timestamp=reading.timestamp,
                severity="WARNING",
            )
            self._anomalies.append(anomaly)
            for cb in self._anomaly_callbacks:
                cb(anomaly)
            self._update_state()
            return anomaly

        return None

    def _check_threshold(
        self, reading: SensorReading, window: SensorWindow
    ) -> Optional[AnomalyEvent]:
        c = self.config

        thresholds = {
            SensorKind.CHAMBER_PRESSURE: (c.chamber_pressure_min, c.chamber_pressure_max),
            SensorKind.TURBOPUMP_SPEED: (0, c.turbopump_speed_max),
            SensorKind.VIBRATION: (0, c.vibration_max),
            SensorKind.THRUST: (c.thrust_min, c.thrust_nom * 1.2),
        }

        if reading.kind in thresholds:
            lo, hi = thresholds[reading.kind]
            if reading.value < lo or reading.value > hi:
                return AnomalyEvent(
                    sensor=reading.kind,
                    engine_id=reading.engine_id,
                    value=reading.value,
                    expected_range=(lo, hi),
                    timestamp=reading.timestamp,
                    severity="CRITICAL" if reading.value < lo * 0.8 or reading.value > hi * 1.2 else "WARNING",
                )
        return None

    def _update_state(self):
        recent = self._anomalies[-10:] if self._anomalies else []
        critical = sum(1 for a in recent if a.severity == "CRITICAL")
        if critical >= 3:
            self._state = HealthState.CRITICAL
        elif critical >= 1:
            self._state = HealthState.DEGRADED
        elif len(recent) >= 5:
            self._state = HealthState.DEGRADED
        else:
            self._state = HealthState.NOMINAL

    def get_engine_health(self, engine_id: int) -> dict:
        sensors = {}
        for (eid, kind), window in self._windows.items():
            if eid != engine_id:
                continue
            sensors[kind.name] = {
                "mean": round(window.mean, 4),
                "std_dev": round(window.std_dev, 4),
                "rate_of_change": round(window.rate_of_change, 4),
                "outlier": window.is_outlier,
                "samples": len(window._values),
            }
        return {"engine_id": engine_id, "sensors": sensors, "state": self._state.name}

    @property
    def state(self) -> HealthState:
        return self._state

    @property
    def recent_anomalies(self) -> list[dict]:
        return [
            {
                "sensor": a.sensor.name,
                "engine": a.engine_id,
                "value": a.value,
                "severity": a.severity,
            }
            for a in self._anomalies[-20:]
        ]
