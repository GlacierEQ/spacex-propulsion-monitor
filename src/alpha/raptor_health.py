"""Repository-local multi-sensor health evaluation.

The historical public class name ``RaptorHealthMonitor`` is retained as a
compatibility alias only. This module consumes caller-supplied synthetic/local
samples; it is not connected to SpaceX, Raptor, Merlin, flight hardware, or
proprietary telemetry.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Optional

EVIDENCE_STATE = "LOCAL_PROPULSION_HEALTH_SIMULATION_NOT_FLIGHT_ENGINE_AUTHORITY"


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


def _validate_engine_id(engine_id: object) -> int:
    if isinstance(engine_id, bool) or not isinstance(engine_id, int):
        raise ValueError("engine_id must be a non-boolean integer")
    if engine_id < 0:
        raise ValueError("engine_id must be non-negative")
    return engine_id


@dataclass(frozen=True)
class EngineConfig:
    """Illustrative local fixture thresholds, not vehicle specifications."""

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

    def validate(self) -> None:
        values = self.__dict__.values()
        if any(not math.isfinite(value) or value <= 0 for value in values):
            raise ValueError("fixture thresholds must be finite and positive")
        if not (
            self.chamber_pressure_min
            <= self.chamber_pressure_nom
            <= self.chamber_pressure_max
        ):
            raise ValueError("chamber pressure fixture thresholds are inconsistent")
        if self.thrust_min > self.thrust_nom:
            raise ValueError("thrust fixture thresholds are inconsistent")


@dataclass(frozen=True)
class SensorReading:
    kind: SensorKind
    value: float
    timestamp: float
    engine_id: int = 0

    def validate(self) -> None:
        if not isinstance(self.kind, SensorKind):
            raise ValueError("sensor kind must be a SensorKind")
        if not math.isfinite(self.value):
            raise ValueError("sensor value must be finite")
        if not math.isfinite(self.timestamp):
            raise ValueError("sensor timestamp must be finite")
        _validate_engine_id(self.engine_id)


class SensorWindow:
    def __init__(self, size: int = 50):
        if size < 2:
            raise ValueError("window size must be at least 2")
        self.size = size
        self._values: list[float] = []
        self._timestamps: list[float] = []

    def push(self, value: float, timestamp: float) -> None:
        if not math.isfinite(value) or not math.isfinite(timestamp):
            raise ValueError("window samples must be finite")
        if self._timestamps and timestamp < self._timestamps[-1]:
            raise ValueError("sensor timestamps must be monotonic")
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
        mean = self.mean
        return sum((value - mean) ** 2 for value in self._values) / (
            len(self._values) - 1
        )

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
        mean = self.mean
        std_dev = self.std_dev
        if std_dev < 1e-10:
            return abs(latest - mean) > 1e-6
        return abs((latest - mean) / std_dev) > 3.0


@dataclass(frozen=True)
class AnomalyEvent:
    sensor: SensorKind
    engine_id: int
    value: float
    expected_range: tuple[float, float]
    timestamp: float
    severity: str = "WARNING"


class EquipmentHealthMonitor:
    """Evaluate local samples independently for each simulated equipment unit."""

    _STATE_RANK = {
        HealthState.NOMINAL: 0,
        HealthState.DEGRADED: 1,
        HealthState.CRITICAL: 2,
        HealthState.OFFLINE: 3,
    }
    _HEALTH_WINDOW = 10
    _ANOMALY_HISTORY = 100

    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self.config.validate()
        self._windows: dict[tuple[int, SensorKind], SensorWindow] = {}
        self._anomalies: deque[AnomalyEvent] = deque(maxlen=self._ANOMALY_HISTORY)
        self._recent_health: dict[int, list[HealthState]] = {}
        self._engine_states: dict[int, HealthState] = {}
        self._anomaly_callbacks: list[Callable[[AnomalyEvent], None]] = []
        self._callback_failures = 0

    def _get_window(self, engine_id: int, kind: SensorKind) -> SensorWindow:
        key = (engine_id, kind)
        if key not in self._windows:
            self._windows[key] = SensorWindow()
        return self._windows[key]

    def on_anomaly(self, callback: Callable[[AnomalyEvent], None]) -> None:
        self._anomaly_callbacks.append(callback)

    def _notify_anomaly(self, anomaly: AnomalyEvent) -> None:
        for callback in self._anomaly_callbacks:
            try:
                callback(anomaly)
            except Exception:
                self._callback_failures += 1

    def ingest(self, reading: SensorReading) -> Optional[AnomalyEvent]:
        reading.validate()
        window = self._get_window(reading.engine_id, reading.kind)
        window.push(reading.value, reading.timestamp)

        anomaly = self._check_threshold(reading)
        if anomaly is None and window.is_outlier:
            anomaly = AnomalyEvent(
                sensor=reading.kind,
                engine_id=reading.engine_id,
                value=reading.value,
                expected_range=(
                    window.mean - 3 * window.std_dev,
                    window.mean + 3 * window.std_dev,
                ),
                timestamp=reading.timestamp,
                severity="WARNING",
            )

        if anomaly is not None:
            self._anomalies.append(anomaly)
            sample_state = (
                HealthState.CRITICAL
                if anomaly.severity == "CRITICAL"
                else HealthState.DEGRADED
            )
            self._record_health(reading.engine_id, sample_state)
            self._notify_anomaly(anomaly)
        else:
            self._record_health(reading.engine_id, HealthState.NOMINAL)
        return anomaly

    def _record_health(self, engine_id: int, sample_state: HealthState) -> None:
        history = self._recent_health.setdefault(engine_id, [])
        history.append(sample_state)
        if len(history) > self._HEALTH_WINDOW:
            del history[:-self._HEALTH_WINDOW]
        self._update_state(engine_id)

    def _check_threshold(self, reading: SensorReading) -> Optional[AnomalyEvent]:
        config = self.config
        thresholds = {
            SensorKind.CHAMBER_PRESSURE: (
                config.chamber_pressure_min,
                config.chamber_pressure_max,
            ),
            SensorKind.TURBOPUMP_SPEED: (0.0, config.turbopump_speed_max),
            SensorKind.VIBRATION: (0.0, config.vibration_max),
            SensorKind.THRUST: (config.thrust_min, config.thrust_nom * 1.2),
        }
        bounds = thresholds.get(reading.kind)
        if bounds is None:
            return None
        low, high = bounds
        if low <= reading.value <= high:
            return None
        severe_low = low > 0 and reading.value < low * 0.8
        severe_high = reading.value > high * 1.2
        return AnomalyEvent(
            sensor=reading.kind,
            engine_id=reading.engine_id,
            value=reading.value,
            expected_range=(low, high),
            timestamp=reading.timestamp,
            severity="CRITICAL" if severe_low or severe_high else "WARNING",
        )

    def _update_state(self, engine_id: int) -> None:
        history = self._recent_health.get(engine_id, [])[-self._HEALTH_WINDOW :]
        critical = sum(state == HealthState.CRITICAL for state in history)
        degraded = sum(state == HealthState.DEGRADED for state in history)
        if critical >= 3:
            state = HealthState.CRITICAL
        elif critical >= 1 or degraded >= 5:
            state = HealthState.DEGRADED
        else:
            state = HealthState.NOMINAL
        self._engine_states[engine_id] = state

    def state_for(self, engine_id: int) -> HealthState:
        engine_id = _validate_engine_id(engine_id)
        return self._engine_states.get(engine_id, HealthState.NOMINAL)

    def get_engine_health(self, engine_id: int) -> dict:
        engine_id = _validate_engine_id(engine_id)
        sensors: dict[str, dict] = {}
        for (sample_engine_id, kind), window in self._windows.items():
            if sample_engine_id != engine_id:
                continue
            sensors[kind.name] = {
                "mean": round(window.mean, 4),
                "std_dev": round(window.std_dev, 4),
                "rate_of_change": round(window.rate_of_change, 4),
                "outlier": window.is_outlier,
                "samples": len(window._values),
            }
        return {
            "engine_id": engine_id,
            "sensors": sensors,
            "state": self.state_for(engine_id).name,
            "evidence_state": EVIDENCE_STATE,
        }

    @property
    def state(self) -> HealthState:
        if not self._engine_states:
            return HealthState.NOMINAL
        return max(
            self._engine_states.values(),
            key=lambda state: self._STATE_RANK[state],
        )

    @property
    def recent_anomalies(self) -> list[dict]:
        return [
            {
                "sensor": anomaly.sensor.name,
                "engine": anomaly.engine_id,
                "value": anomaly.value,
                "expected_range": list(anomaly.expected_range),
                "timestamp": anomaly.timestamp,
                "severity": anomaly.severity,
                "evidence_state": EVIDENCE_STATE,
            }
            for anomaly in list(self._anomalies)[-20:]
        ]

    @property
    def callback_failures(self) -> int:
        return self._callback_failures


# Historical compatibility alias. It does not imply Raptor data or authority.
RaptorHealthMonitor = EquipmentHealthMonitor
