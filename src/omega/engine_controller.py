"""Engine controller — manages engine state machine, throttle profiles, and shutdown logic.

Coordinates multi-engine operations for Falcon 9 (9 engines) or Starship (33 engines).
Implements engine-out capability and graceful degradation.
"""

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable

from alpha.raptor_health import RaptorHealthMonitor, HealthState, SensorReading, SensorKind


class EngineMode(Enum):
    OFF = auto()
    STARTUP = auto()
    IDLE = auto()
    NOMINAL = auto()
    THROTTLE_DOWN = auto()
    SHUTDOWN = auto()
    EMERGENCY_STOP = auto()


@dataclass
class EngineState:
    engine_id: int
    mode: EngineMode = EngineMode.OFF
    throttle_percent: float = 0.0
    health: HealthState = HealthState.NOMINAL
    run_time: float = 0.0
    start_time: float = 0.0
    shutdown_reason: str = ""


@dataclass
class ThrottleProfile:
    name: str
    points: list[tuple[float, float]]

    def get_throttle(self, t: float) -> float:
        if not self.points:
            return 100.0
        if t <= self.points[0][0]:
            return self.points[0][1]
        if t >= self.points[-1][0]:
            return self.points[-1][1]

        for i in range(len(self.points) - 1):
            t0, v0 = self.points[i]
            t1, v1 = self.points[i + 1]
            if t0 <= t <= t1:
                frac = (t - t0) / (t1 - t0) if t1 != t0 else 0
                return v0 + frac * (v1 - v0)
        return 100.0


class EngineController:
    def __init__(self, engine_count: int = 9, config=None):
        self.engine_count = engine_count
        self.health_monitor = RaptorHealthMonitor(config)
        self._engines: dict[int, EngineState] = {
            i: EngineState(engine_id=i) for i in range(engine_count)
        }
        self._profiles: dict[str, ThrottleProfile] = {}
        self._active_profile: Optional[str] = None
        self._mission_start: float = 0.0
        self._shutdown_callbacks: list[Callable] = []
        self._event_log: list[dict] = []

    def add_profile(self, profile: ThrottleProfile):
        self._profiles[profile.name] = profile

    def on_shutdown(self, callback: Callable):
        self._shutdown_callbacks.append(callback)

    def start_engines(self) -> dict:
        if self._mission_start == 0:
            self._mission_start = time.time()

        for eid, state in self._engines.items():
            state.mode = EngineMode.STARTUP
            state.start_time = time.time()
            self._log(f"engine_{eid}_startup")

        return {"action": "STARTUP", "engines": self.engine_count}

    def set_throttle(self, engine_id: int, percent: float) -> bool:
        state = self._engines.get(engine_id)
        if not state or state.mode in (EngineMode.OFF, EngineMode.SHUTDOWN):
            return False

        percent = max(0, min(100, percent))
        state.throttle_percent = percent

        if percent < 40:
            state.mode = EngineMode.THROTTLE_DOWN
        elif state.mode in (EngineMode.THROTTLE_DOWN, EngineMode.STARTUP, EngineMode.IDLE):
            state.mode = EngineMode.NOMINAL

        return True

    def apply_profile(self, profile_name: str, mission_time: float) -> dict:
        profile = self._profiles.get(profile_name)
        if not profile:
            return {"error": f"profile {profile_name} not found"}

        throttle = profile.get_throttle(mission_time)
        results = []

        for eid, state in self._engines.items():
            if state.mode in (EngineMode.OFF, EngineMode.SHUTDOWN):
                continue
            state.throttle_percent = throttle
            results.append({"engine": eid, "throttle": throttle})

        return {"profile": profile_name, "throttle": throttle, "engines": results}

    def shutdown_engine(self, engine_id: int, reason: str = "manual") -> bool:
        state = self._engines.get(engine_id)
        if not state or state.mode == EngineMode.OFF:
            return False

        state.mode = EngineMode.SHUTDOWN
        state.throttle_percent = 0.0
        state.shutdown_reason = reason
        self._log(f"engine_{engine_id}_shutdown: {reason}")

        for cb in self._shutdown_callbacks:
            cb({"engine_id": engine_id, "reason": reason})

        return True

    def emergency_stop(self, reason: str = "auto") -> dict:
        stopped = []
        for eid in range(self.engine_count):
            state = self._engines[eid]
            if state.mode != EngineMode.OFF:
                state.mode = EngineMode.EMERGENCY_STOP
                state.throttle_percent = 0.0
                state.shutdown_reason = reason
                stopped.append(eid)
                self._log(f"engine_{eid}_EMERGENCY_STOP: {reason}")

        return {"action": "EMERGENCY_STOP", "stopped": stopped, "reason": reason}

    def process_telemetry(self, sensor_id: int, kind: SensorKind, value: float):
        reading = SensorReading(kind=kind, value=value, timestamp=time.time(), engine_id=sensor_id)
        anomaly = self.health_monitor.ingest(reading)

        if anomaly and anomaly.severity == "CRITICAL":
            state = self._engines.get(sensor_id)
            if state and state.mode != EngineMode.OFF:
                self.shutdown_engine(sensor_id, f"critical: {anomaly.sensor.name}")

        state = self._engines.get(sensor_id)
        if state:
            state.health = self.health_monitor.state

    def get_vehicle_status(self) -> dict:
        modes = {}
        total_throttle = 0.0
        active_count = 0

        for eid, state in self._engines.items():
            modes[state.mode.name] = modes.get(state.mode.name, 0) + 1
            if state.mode not in (EngineMode.OFF, EngineMode.SHUTDOWN):
                total_throttle += state.throttle_percent
                active_count += 1

        avg_throttle = total_throttle / active_count if active_count > 0 else 0

        return {
            "engines_total": self.engine_count,
            "engines_active": active_count,
            "mode_distribution": modes,
            "average_throttle": round(avg_throttle, 1),
            "mission_time": round(time.time() - self._mission_start, 1) if self._mission_start else 0,
            "health_state": self.health_monitor.state.name,
        }

    def _log(self, event: str):
        self._event_log.append({"time": time.time(), "event": event})

    @property
    def event_log(self) -> list[dict]:
        return list(self._event_log)
