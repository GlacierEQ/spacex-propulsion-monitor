"""Local state-transition and diagnostic heuristic package."""

from .engine_controller import EngineController, EngineMode, EngineState, ThrottleProfile
from .predictive_health import (
    CrossSensorCorrelator,
    DegradationModel,
    FailurePrediction,
    SensorTimeSeries,
    TrendExtrapolator,
    VibrationSpectralAnalyzer,
)

__all__ = [
    "CrossSensorCorrelator",
    "DegradationModel",
    "EngineController",
    "EngineMode",
    "EngineState",
    "FailurePrediction",
    "SensorTimeSeries",
    "ThrottleProfile",
    "TrendExtrapolator",
    "VibrationSpectralAnalyzer",
]
