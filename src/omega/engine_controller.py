"""Repository-local multi-unit state-transition simulator.

The historical ``EngineController`` name is preserved for compatibility. All
start, throttle, shutdown, and emergency-stop operations mutate in-memory state
only; this module has no flight-hardware, engine-command, or SpaceX authority.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Optional

from alpha.raptor_health import (
    EVIDENCE_STATE,
    EngineConfig,
    HealthState,
    RaptorHealthMonitor,
    SensorKind,
    SensorReading,
)


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


@dataclass(frozen=True)
class ThrottleProfile:
    name: str
    points: list[tuple[float, float]]

    def validate(self) -> None:
        if not self.name:
            raise ValueError("profile name required")
        if not self.points:
            raise ValueError("profile requires at least one throttle point")
        previous_time = -math.inf
        for timestamp, throttle in self.points:
            if not math.isfinite(timestamp) or timestamp < 0:
                raise ValueError("profile times must be finite and non-negative")
            if timestamp < previous_time:
                raise ValueError("profile times must be ordered")
            if not math.isfinite(throttle) or not 0 <= throttle <= 100:
                raise ValueError("profile throttle must be in 0..100")
            previous_time = timestamp

    def get_throttle(self, elapsed_s: float) -> float:
        self.validate()
        if not math.isfinite(elapsed_s) or elapsed_s < 0:
            raise ValueError("elapsed_s must be finite and non-negative")
        if elapsed_s <= self.points[0][0]:
            return self.points[0][1]
        if elapsed_s >= self.points[-1][0]:
            return self.points[-1][1]

        for index in range(len(self.points) - 1):
            t0, v0 = self.points[index]
            t1, v1 = self.points[index + 1]
            if t0 <= elapsed_s <= t1:
                fraction = (elapsed_s - t0) / (t1 - t0) if t1 != t0 else 0.0
                return v0 + fraction * (v1 - v0)
        return self.points[-1][1]


class EngineController:
    """In-memory simulated engine-state coordinator; no external side effects."""

    _EVENT_HISTORY = 200

    def __init__(self, engine_count: int = 9, config: Optional[EngineConfig] = None):
        if (
            isinstance(engine_count, bool)
            or not isinstance(engine_count, int)
            or engine_count <= 0
        ):
            raise ValueError("engine_count must be a positive non-boolean integer")
        self.engine_count = engine_count
        self.health_monitor = RaptorHealthMonitor(config)
        self._engines: dict[int, EngineState] = {
            engine_id: EngineState(engine_id=engine_id)
            for engine_id in range(engine_count)
        }
        self._profiles: dict[str, ThrottleProfile] = {}
        self._active_profile: Optional[str] = None
        self._simulation_start: float = 0.0
        self._shutdown_callbacks: list[Callable[[dict], None]] = []
        self._callback_failures = 0
        self._event_log: list[dict] = []

    def _require_engine_id(self, engine_id: object) -> int:
        if isinstance(engine_id, bool) or not isinstance(engine_id, int):
            raise ValueError("engine_id must be a non-boolean integer")
        if engine_id not in self._engines:
            raise ValueError("engine_id is outside the simulated fleet")
        return engine_id

    def add_profile(self, profile: ThrottleProfile) -> None:
        profile.validate()
        self._profiles[profile.name] = profile

    def on_shutdown(self, callback: Callable[[dict], None]) -> None:
        self._shutdown_callbacks.append(callback)

    def _notify_shutdown(self, payload: dict) -> None:
        for callback in self._shutdown_callbacks:
            try:
                callback(payload)
            except Exception:
                self._callback_failures += 1

    def start_engines(self) -> dict:
        if self._simulation_start == 0:
            self._simulation_start = time.monotonic()

        for engine_id, state in self._engines.items():
            state.mode = EngineMode.STARTUP
            state.start_time = time.monotonic()
            self._log(f"unit_{engine_id}_startup")

        return {
            "action": "SIMULATED_STARTUP",
            "engines": self.engine_count,
            "evidence_state": EVIDENCE_STATE,
        }

    def set_throttle(self, engine_id: int, percent: float) -> bool:
        if not math.isfinite(percent) or not 0 <= percent <= 100:
            raise ValueError("simulated throttle must be finite and in 0..100")
        engine_id = self._require_engine_id(engine_id)
        state = self._engines[engine_id]
        if state.mode in (
            EngineMode.OFF,
            EngineMode.SHUTDOWN,
            EngineMode.EMERGENCY_STOP,
        ):
            return False

        state.throttle_percent = percent
        if percent < 40:
            state.mode = EngineMode.THROTTLE_DOWN
        elif state.mode in (
            EngineMode.THROTTLE_DOWN,
            EngineMode.STARTUP,
            EngineMode.IDLE,
        ):
            state.mode = EngineMode.NOMINAL
        return True

    def apply_profile(self, profile_name: str, elapsed_s: float) -> dict:
        profile = self._profiles.get(profile_name)
        if profile is None:
            return {
                "error": f"profile {profile_name} not found",
                "evidence_state": EVIDENCE_STATE,
            }

        throttle = profile.get_throttle(elapsed_s)
        self._active_profile = profile_name
        results = []
        for engine_id in self._engines:
            if self.set_throttle(engine_id, throttle):
                results.append({"engine": engine_id, "throttle": throttle})

        return {
            "profile": profile_name,
            "throttle": throttle,
            "engines": results,
            "evidence_state": EVIDENCE_STATE,
        }

    def shutdown_engine(self, engine_id: int, reason: str = "manual") -> bool:
        engine_id = self._require_engine_id(engine_id)
        state = self._engines[engine_id]
        if state.mode in (
            EngineMode.OFF,
            EngineMode.SHUTDOWN,
            EngineMode.EMERGENCY_STOP,
        ):
            return False

        state.mode = EngineMode.SHUTDOWN
        state.throttle_percent = 0.0
        state.shutdown_reason = str(reason)
        self._log(f"unit_{engine_id}_shutdown")
        self._notify_shutdown(
            {
                "engine_id": engine_id,
                "reason": str(reason),
                "mode": EngineMode.SHUTDOWN.name,
                "evidence_state": EVIDENCE_STATE,
            }
        )
        return True

    def emergency_stop(self, reason: str = "local simulation") -> dict:
        stopped = []
        terminal_modes = {
            EngineMode.OFF,
            EngineMode.SHUTDOWN,
            EngineMode.EMERGENCY_STOP,
        }
        for engine_id in range(self.engine_count):
            state = self._engines[engine_id]
            if state.mode in terminal_modes:
                continue
            state.mode = EngineMode.EMERGENCY_STOP
            state.throttle_percent = 0.0
            state.shutdown_reason = str(reason)
            stopped.append(engine_id)
            self._log(f"unit_{engine_id}_emergency_stop")
            self._notify_shutdown(
                {
                    "engine_id": engine_id,
                    "reason": str(reason),
                    "mode": EngineMode.EMERGENCY_STOP.name,
                    "evidence_state": EVIDENCE_STATE,
                }
            )

        return {
            "action": "SIMULATED_EMERGENCY_STOP",
            "stopped": stopped,
            "reason": str(reason),
            "evidence_state": EVIDENCE_STATE,
        }

    def process_telemetry(
        self,
        engine_id: int,
        kind: SensorKind,
        value: float,
        *,
        timestamp: Optional[float] = None,
    ) -> Optional[dict]:
        """Process one local sample in a single Unix wall-clock time domain.

        ``timestamp`` is seconds since the Unix epoch. When omitted, ``time.time``
        supplies the timestamp. Explicit and implicit samples for the same
        engine/sensor pair must therefore be nondecreasing in the same domain.
        """
        engine_id = self._require_engine_id(engine_id)
        sample_time = time.time() if timestamp is None else timestamp
        reading = SensorReading(
            kind=kind,
            value=value,
            timestamp=sample_time,
            engine_id=engine_id,
        )
        anomaly = self.health_monitor.ingest(reading)

        if anomaly is not None and anomaly.severity == "CRITICAL":
            state = self._engines[engine_id]
            if state.mode not in (
                EngineMode.OFF,
                EngineMode.SHUTDOWN,
                EngineMode.EMERGENCY_STOP,
            ):
                self.shutdown_engine(engine_id, f"critical:{anomaly.sensor.name}")

        self._engines[engine_id].health = self.health_monitor.state_for(engine_id)
        if anomaly is None:
            return None
        return {
            "engine_id": anomaly.engine_id,
            "sensor": anomaly.sensor.name,
            "severity": anomaly.severity,
            "evidence_state": EVIDENCE_STATE,
        }

    def get_vehicle_status(self) -> dict:
        modes: dict[str, int] = {}
        total_throttle = 0.0
        active_count = 0

        for state in self._engines.values():
            modes[state.mode.name] = modes.get(state.mode.name, 0) + 1
            if state.mode not in (
                EngineMode.OFF,
                EngineMode.SHUTDOWN,
                EngineMode.EMERGENCY_STOP,
            ):
                total_throttle += state.throttle_percent
                active_count += 1

        average_throttle = total_throttle / active_count if active_count else 0.0
        elapsed = (
            time.monotonic() - self._simulation_start
            if self._simulation_start
            else 0.0
        )
        return {
            "engines_total": self.engine_count,
            "engines_active": active_count,
            "mode_distribution": modes,
            "average_throttle": round(average_throttle, 1),
            "simulation_time": round(elapsed, 3),
            "health_state": self.health_monitor.state.name,
            "active_profile": self._active_profile,
            "evidence_state": EVIDENCE_STATE,
        }

    def _log(self, event: str) -> None:
        self._event_log.append({"time": time.time(), "event": event})
        if len(self._event_log) > self._EVENT_HISTORY:
            del self._event_log[:-self._EVENT_HISTORY]

    @property
    def event_log(self) -> list[dict]:
        return list(self._event_log)

    @property
    def callback_failures(self) -> int:
        return self._callback_failures
