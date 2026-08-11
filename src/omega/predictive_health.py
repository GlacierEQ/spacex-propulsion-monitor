"""Repository-local diagnostic heuristics for synthetic sensor series.

This module contains reusable trend projection, correlation, degradation-fit,
and vibration-spectrum mechanisms. Outputs are heuristic scores and threshold
projection horizons, not validated failure probabilities, remaining-useful-life
predictions, Raptor/Merlin models, or flight-control signals.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

EVIDENCE_STATE = "LOCAL_PROPULSION_HEALTH_SIMULATION_NOT_FLIGHT_ENGINE_AUTHORITY"


def _finite(value: float, label: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    return value


@dataclass
class SensorTimeSeries:
    sensor_name: str
    engine_id: int
    values: list[float] = field(default_factory=list)
    timestamps: list[float] = field(default_factory=list)

    def append(self, value: float, timestamp: float) -> None:
        if not self.sensor_name:
            raise ValueError("sensor_name required")
        if self.engine_id < 0:
            raise ValueError("engine_id must be non-negative")
        _finite(value, "value")
        _finite(timestamp, "timestamp")
        if self.timestamps and timestamp < self.timestamps[-1]:
            raise ValueError("timestamps must be monotonic")
        self.values.append(value)
        self.timestamps.append(timestamp)
        if len(self.values) > 500:
            self.values = self.values[-500:]
            self.timestamps = self.timestamps[-500:]

    @property
    def latest(self) -> float:
        return self.values[-1] if self.values else 0.0

    @property
    def mean(self) -> float:
        return sum(self.values) / len(self.values) if self.values else 0.0

    @property
    def count(self) -> int:
        return len(self.values)


@dataclass(frozen=True)
class FailurePrediction:
    """Compatibility record for a heuristic diagnostic warning.

    ``confidence`` is a bounded heuristic score, not calibrated probability.
    ``predicted_time_s`` is a projected threshold-crossing horizon.
    """

    engine_id: int
    failure_mode: str
    predicted_time_s: float
    confidence: float
    evidence: list[str]
    severity: str


class TrendExtrapolator:
    """Project a local linear trend to an illustrative threshold."""

    def __init__(self, history_window: int = 100):
        if history_window < 10:
            raise ValueError("history_window must be at least 10")
        self.history_window = history_window

    def extrapolate_to_threshold(
        self,
        series: SensorTimeSeries,
        threshold: float,
        direction: str = "above",
    ) -> Optional[dict]:
        _finite(threshold, "threshold")
        if direction not in {"above", "below"}:
            raise ValueError("direction must be above or below")
        if series.count < 10:
            return None

        values = series.values[-self.history_window :]
        times = series.timestamps[-self.history_window :]
        n = len(values)
        time_mean = sum(times) / n
        value_mean = sum(values) / n
        ss_tt = sum((timestamp - time_mean) ** 2 for timestamp in times)
        if ss_tt < 1e-15:
            return None
        ss_tv = sum(
            (times[index] - time_mean) * (values[index] - value_mean)
            for index in range(n)
        )
        slope = ss_tv / ss_tt
        intercept = value_mean - slope * time_mean
        current = values[-1]

        moving_toward = (direction == "above" and slope > 0) or (
            direction == "below" and slope < 0
        )
        if not moving_toward:
            return None
        horizon = (threshold - current) / slope
        if horizon < 0 or not math.isfinite(horizon):
            return None

        residuals = [
            values[index] - (slope * times[index] + intercept)
            for index in range(n)
        ]
        ss_res = sum(residual**2 for residual in residuals)
        if n > 2 and ss_res > 0:
            slope_error = math.sqrt(ss_res / (n - 2) / ss_tt)
            significance = abs(slope / slope_error) if slope_error > 0 else 0.0
            fit_score = min(0.95, significance / 3.0)
        else:
            fit_score = 0.95 if abs(slope) > 0 else 0.0

        return {
            "time_to_threshold_s": horizon,
            "current_value": current,
            "threshold": threshold,
            "slope_per_s": slope,
            "confidence": max(0.0, min(0.95, fit_score)),
            "score_semantics": "heuristic_fit_not_probability",
            "evidence_state": EVIDENCE_STATE,
        }


class CrossSensorCorrelator:
    """Compute bounded Pearson correlation on aligned local sample windows."""

    def __init__(self, window_size: int = 50, correlation_threshold: float = 0.7):
        if window_size < 10:
            raise ValueError("window_size must be at least 10")
        if not 0 <= correlation_threshold <= 1:
            raise ValueError("correlation_threshold must be in 0..1")
        self.window_size = window_size
        self.correlation_threshold = correlation_threshold
        self._series: dict[str, SensorTimeSeries] = {}

    def register_sensor(self, key: str, series: SensorTimeSeries) -> None:
        if not key:
            raise ValueError("sensor key required")
        self._series[key] = series

    def compute_correlation(self, key_a: str, key_b: str) -> Optional[float]:
        if key_a not in self._series or key_b not in self._series:
            return None
        left = self._series[key_a]
        right = self._series[key_b]
        n = min(left.count, right.count, self.window_size)
        if n < 10:
            return None
        left_values = left.values[-n:]
        right_values = right.values[-n:]
        left_mean = sum(left_values) / n
        right_mean = sum(right_values) / n
        left_dev = [value - left_mean for value in left_values]
        right_dev = [value - right_mean for value in right_values]
        covariance = sum(
            left_dev[index] * right_dev[index] for index in range(n)
        ) / n
        left_var = sum(value**2 for value in left_dev) / n
        right_var = sum(value**2 for value in right_dev) / n
        if left_var < 1e-15 or right_var < 1e-15:
            return None
        return max(
            -1.0,
            min(1.0, covariance / math.sqrt(left_var * right_var)),
        )

    def detect_correlated_anomalies(self) -> list[dict]:
        anomalies: list[dict] = []
        keys = sorted(self._series)
        for left_index in range(len(keys)):
            for right_index in range(left_index + 1, len(keys)):
                key_a = keys[left_index]
                key_b = keys[right_index]
                correlation = self.compute_correlation(key_a, key_b)
                if correlation is None or abs(correlation) <= self.correlation_threshold:
                    continue
                left = self._series[key_a]
                right = self._series[key_b]
                left_scale = max(abs(left.mean), 1e-10)
                right_scale = max(abs(right.mean), 1e-10)
                left_deviation = abs(left.latest - left.mean) / left_scale
                right_deviation = abs(right.latest - right.mean) / right_scale
                if left_deviation <= 0.1 and right_deviation <= 0.1:
                    continue
                anomalies.append(
                    {
                        "sensor_a": key_a,
                        "sensor_b": key_b,
                        "correlation": correlation,
                        "a_deviation": left_deviation,
                        "b_deviation": right_deviation,
                        "evidence_state": EVIDENCE_STATE,
                    }
                )
        return anomalies


class DegradationModel:
    """Fit simple illustrative degradation curves to local sample sequences."""

    def __init__(self):
        self._models: dict[str, dict] = {}

    def fit_bearing_wear(self, sensor_key: str, vibration_data: list[float]) -> dict:
        if len(vibration_data) < 20:
            return {"fitted": False, "evidence_state": EVIDENCE_STATE}
        if any(not math.isfinite(value) or value < 0 for value in vibration_data):
            raise ValueError("vibration samples must be finite and non-negative")
        n = len(vibration_data)
        times = list(range(n))
        time_mean = sum(times) / n
        value_mean = sum(vibration_data) / n
        ss_tt = sum((timestamp - time_mean) ** 2 for timestamp in times)
        if ss_tt < 1e-15:
            return {"fitted": False, "evidence_state": EVIDENCE_STATE}
        ss_tv = sum(
            (times[index] - time_mean) * (vibration_data[index] - value_mean)
            for index in range(n)
        )
        slope = ss_tv / ss_tt
        intercept = value_mean - slope * time_mean
        fixture_threshold = max(value_mean * 3.0, 1e-10)
        horizon = (
            (fixture_threshold - vibration_data[-1]) / slope
            if slope > 0
            else math.inf
        )
        horizon = max(0.0, horizon) if math.isfinite(horizon) else math.inf
        residuals = [
            vibration_data[index] - (slope * times[index] + intercept)
            for index in range(n)
        ]
        noise_variance = sum(value**2 for value in residuals) / max(n - 2, 1)
        uncertainty = math.sqrt(noise_variance) * 2
        model = {
            "type": "linear_vibration_trend",
            "slope": slope,
            "intercept": intercept,
            "fixture_threshold": fixture_threshold,
            "time_to_failure_samples": horizon,
            "uncertainty": uncertainty,
            "semantics": "illustrative_threshold_horizon_not_rul",
        }
        self._models[sensor_key] = model
        return {
            "fitted": True,
            "degradation_rate": slope,
            "time_to_failure_samples": horizon,
            "uncertainty": uncertainty,
            "semantics": model["semantics"],
            "evidence_state": EVIDENCE_STATE,
        }

    def fit_turbine_erosion(self, sensor_key: str, efficiency_data: list[float]) -> dict:
        if len(efficiency_data) < 20:
            return {"fitted": False, "evidence_state": EVIDENCE_STATE}
        if any(
            not math.isfinite(value) or value <= 0 for value in efficiency_data
        ):
            raise ValueError("efficiency samples must be finite and positive")
        n = len(efficiency_data)
        times = list(range(n))
        log_values = [math.log(value) for value in efficiency_data]
        time_mean = sum(times) / n
        log_mean = sum(log_values) / n
        ss_tt = sum((timestamp - time_mean) ** 2 for timestamp in times)
        if ss_tt < 1e-15:
            return {"fitted": False, "evidence_state": EVIDENCE_STATE}
        ss_te = sum(
            (times[index] - time_mean) * (log_values[index] - log_mean)
            for index in range(n)
        )
        decay_rate = ss_te / ss_tt
        fixture_threshold = 0.7
        current = efficiency_data[-1]
        if current <= fixture_threshold:
            horizon = 0.0
        elif decay_rate < 0:
            horizon = math.log(fixture_threshold / current) / decay_rate
        else:
            horizon = math.inf
        self._models[sensor_key] = {
            "type": "exponential_efficiency_trend",
            "decay_rate": decay_rate,
            "fixture_threshold": fixture_threshold,
            "time_to_failure_samples": horizon,
            "semantics": "illustrative_threshold_horizon_not_rul",
        }
        return {
            "fitted": True,
            "decay_rate": decay_rate,
            "time_to_failure_samples": horizon,
            "semantics": "illustrative_threshold_horizon_not_rul",
            "evidence_state": EVIDENCE_STATE,
        }


class VibrationSpectralAnalyzer:
    """Compute a dependency-free discrete spectrum for synthetic vibration data."""

    def __init__(self, sampling_rate_hz: float = 10000.0):
        if not math.isfinite(sampling_rate_hz) or sampling_rate_hz <= 0:
            raise ValueError("sampling_rate_hz must be finite and positive")
        self.sampling_rate = sampling_rate_hz

    def compute_spectrum(
        self,
        vibration_data: list[float],
        window_size: int = 256,
    ) -> dict:
        if window_size < 8:
            raise ValueError("window_size must be at least 8")
        if any(not math.isfinite(value) for value in vibration_data):
            raise ValueError("vibration samples must be finite")
        n = min(len(vibration_data), window_size)
        if n < 8:
            return {
                "frequencies": [],
                "magnitudes": [],
                "peaks": [],
                "evidence_state": EVIDENCE_STATE,
            }
        data = vibration_data[:n]
        mean = sum(data) / n
        centered = [value - mean for value in data]
        magnitudes: list[float] = []
        for frequency_index in range(n // 2):
            real = sum(
                centered[sample_index]
                * math.cos(2 * math.pi * frequency_index * sample_index / n)
                for sample_index in range(n)
            )
            imaginary = sum(
                centered[sample_index]
                * math.sin(2 * math.pi * frequency_index * sample_index / n)
                for sample_index in range(n)
            )
            magnitudes.append(math.hypot(real, imaginary) / n)
        resolution = self.sampling_rate / n
        frequencies = [index * resolution for index in range(n // 2)]
        average_magnitude = sum(magnitudes) / len(magnitudes)
        maximum = max(magnitudes) if magnitudes else 0.0
        peaks = []
        for index in range(1, len(magnitudes) - 1):
            magnitude = magnitudes[index]
            if (
                magnitude > magnitudes[index - 1]
                and magnitude > magnitudes[index + 1]
                and magnitude > average_magnitude * 2
            ):
                peaks.append(
                    {
                        "frequency_hz": frequencies[index],
                        "magnitude": magnitude,
                        "relative_strength": magnitude / maximum if maximum else 0.0,
                    }
                )
        dominant = (
            frequencies[magnitudes.index(maximum)] if magnitudes and maximum else 0.0
        )
        return {
            "frequencies": frequencies,
            "magnitudes": magnitudes,
            "peaks": peaks,
            "total_energy": sum(magnitude**2 for magnitude in magnitudes),
            "dominant_frequency": dominant,
            "evidence_state": EVIDENCE_STATE,
        }

    def classify_fault(self, spectrum: dict) -> Optional[dict]:
        """Return an illustrative spectral signature label, not diagnosis."""
        peaks = spectrum.get("peaks", [])
        if not peaks:
            return None
        dominant = float(spectrum.get("dominant_frequency", 0.0))
        indicators = []
        strong = [peak for peak in peaks if peak["relative_strength"] > 0.5]
        if len(strong) >= 3:
            indicators.append(
                {
                    "fault_type": "MULTI_HARMONIC_SIGNATURE",
                    "confidence": min(0.9, len(strong) / 5),
                    "evidence": f"{len(strong)} strong harmonic peaks",
                }
            )
        low_frequency = [peak for peak in peaks if peak["frequency_hz"] < 100]
        if low_frequency and low_frequency[0]["relative_strength"] > 0.3:
            indicators.append(
                {
                    "fault_type": "LOW_FREQUENCY_SIGNATURE",
                    "confidence": low_frequency[0]["relative_strength"],
                    "evidence": (
                        "low-frequency peak at "
                        f"{low_frequency[0]['frequency_hz']:.1f} Hz"
                    ),
                }
            )
        if not indicators:
            return {
                "fault_type": "NO_CLASSIFIED_SIGNATURE",
                "confidence": 0.0,
                "evidence": "no configured signature matched",
                "score_semantics": "heuristic_not_probability_or_diagnosis",
            }
        result = max(indicators, key=lambda item: item["confidence"])
        result["confidence"] = max(0.0, min(1.0, result["confidence"]))
        result["score_semantics"] = "heuristic_not_probability_or_diagnosis"
        result["dominant_frequency_hz"] = dominant
        return result


class PredictiveHealthMonitor:
    """Fuse local heuristics into bounded diagnostic warnings.

    Historical field names such as ``failure_mode`` are retained for API
    compatibility. They are diagnostic labels, not validated failure forecasts.
    """

    def __init__(self):
        self.trend_extrapolator = TrendExtrapolator()
        self.correlator = CrossSensorCorrelator()
        self.degradation_model = DegradationModel()
        self.vibration_analyzer = VibrationSpectralAnalyzer()
        self._predictions: list[FailurePrediction] = []

    def ingest_sensor_data(
        self,
        engine_id: int,
        sensor_name: str,
        value: float,
        timestamp: float,
    ) -> list[FailurePrediction]:
        if engine_id < 0:
            raise ValueError("engine_id must be non-negative")
        if not sensor_name:
            raise ValueError("sensor_name required")
        _finite(value, "value")
        _finite(timestamp, "timestamp")
        key = f"unit_{engine_id}_{sensor_name}"
        series = self.correlator._series.get(key)
        if series is None:
            series = SensorTimeSeries(sensor_name=sensor_name, engine_id=engine_id)
            self.correlator.register_sensor(key, series)
        series.append(value, timestamp)

        warnings: list[FailurePrediction] = []
        fixture_thresholds = {
            "chamber_pressure": (250.0, 350.0),
            "vibration": (None, 5.0),
            "thrust": (2000000.0, 2800000.0),
        }
        if series.count >= 20 and sensor_name in fixture_thresholds:
            low, high = fixture_thresholds[sensor_name]
            for threshold, direction, label in (
                (high, "above", "OVERLIMIT_TREND"),
                (low, "below", "UNDERLIMIT_TREND"),
            ):
                if threshold is None:
                    continue
                projection = self.trend_extrapolator.extrapolate_to_threshold(
                    series,
                    threshold,
                    direction,
                )
                if projection is None or projection["time_to_threshold_s"] >= 120:
                    continue
                horizon = projection["time_to_threshold_s"]
                warnings.append(
                    FailurePrediction(
                        engine_id=engine_id,
                        failure_mode=f"{sensor_name.upper()}_{label}",
                        predicted_time_s=horizon,
                        confidence=projection["confidence"],
                        evidence=[
                            f"current={projection['current_value']:.4g}",
                            f"slope={projection['slope_per_s']:.4g}/s",
                            f"fixture_threshold={projection['threshold']:.4g}",
                            "heuristic threshold projection; not failure probability",
                        ],
                        severity="CRITICAL" if horizon < 30 else "WARNING",
                    )
                )

        for correlation in self.correlator.detect_correlated_anomalies():
            if key not in {correlation["sensor_a"], correlation["sensor_b"]}:
                continue
            warnings.append(
                FailurePrediction(
                    engine_id=engine_id,
                    failure_mode="CORRELATED_DEVIATION",
                    predicted_time_s=60.0,
                    confidence=abs(correlation["correlation"]),
                    evidence=[
                        f"correlation={correlation['correlation']:.3f}",
                        "heuristic correlation; not causal diagnosis",
                    ],
                    severity="WARNING",
                )
            )

        if sensor_name == "vibration" and series.count >= 256:
            spectrum = self.vibration_analyzer.compute_spectrum(series.values[-256:])
            signature = self.vibration_analyzer.classify_fault(spectrum)
            if signature and signature["fault_type"] not in {
                "NO_CLASSIFIED_SIGNATURE",
            }:
                warnings.append(
                    FailurePrediction(
                        engine_id=engine_id,
                        failure_mode=f"VIBRATION_{signature['fault_type']}",
                        predicted_time_s=90.0,
                        confidence=signature["confidence"],
                        evidence=[
                            signature["evidence"],
                            "heuristic spectral signature; not fault diagnosis",
                        ],
                        severity=(
                            "CRITICAL"
                            if signature["confidence"] > 0.8
                            else "WARNING"
                        ),
                    )
                )

        self._predictions.extend(warnings)
        return warnings

    def get_engine_predictions(self, engine_id: int) -> list[dict]:
        if engine_id < 0:
            raise ValueError("engine_id must be non-negative")
        recent = [
            prediction
            for prediction in self._predictions[-50:]
            if prediction.engine_id == engine_id
        ]
        return [
            {
                "failure_mode": prediction.failure_mode,
                "predicted_time_s": round(prediction.predicted_time_s, 1),
                "confidence": round(prediction.confidence, 2),
                "severity": prediction.severity,
                "evidence": list(prediction.evidence),
                "score_semantics": "heuristic_not_probability_or_diagnosis",
                "evidence_state": EVIDENCE_STATE,
            }
            for prediction in recent
        ]

    @property
    def active_warnings(self) -> int:
        return sum(
            1
            for prediction in self._predictions[-20:]
            if prediction.severity == "WARNING"
        )

    @property
    def active_criticals(self) -> int:
        return sum(
            1
            for prediction in self._predictions[-20:]
            if prediction.severity == "CRITICAL"
        )
