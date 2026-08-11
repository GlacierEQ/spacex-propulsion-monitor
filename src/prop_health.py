#!/usr/bin/env python3
"""Bounded local health-index arithmetic for synthetic propulsion-like samples."""
from __future__ import annotations

import math
from dataclasses import dataclass

EVIDENCE_STATE = "LOCAL_PROPULSION_HEALTH_SIMULATION_NOT_FLIGHT_ENGINE_AUTHORITY"


@dataclass(frozen=True)
class Sample:
    chamber_p_pct: float
    mr_error: float
    vibe_g: float

    def validate(self) -> None:
        values = (self.chamber_p_pct, self.mr_error, self.vibe_g)
        if any(not math.isfinite(value) for value in values):
            raise ValueError("health sample values must be finite")
        if self.chamber_p_pct < 0 or self.mr_error < 0 or self.vibe_g < 0:
            raise ValueError("health sample values must be non-negative")


def health(sample: Sample) -> dict:
    """Return a local fixture score and categorical status; not failure probability."""
    sample.validate()
    pressure_term = max(0.0, 1.0 - abs(sample.chamber_p_pct - 1.0) * 2)
    mixture_term = max(0.0, 1.0 - sample.mr_error * 5)
    vibration_term = max(0.0, 1.0 - sample.vibe_g / 20.0)
    index = 0.45 * pressure_term + 0.35 * mixture_term + 0.20 * vibration_term
    index = max(0.0, min(1.0, index))

    if sample.chamber_p_pct < 0.7 or sample.vibe_g > 15:
        status = "RED"
    elif sample.mr_error > 0.1 or sample.vibe_g > 8:
        status = "YELLOW"
    else:
        status = "GREEN"

    return {
        "health": round(index, 4),
        "status": status,
        "evidence_state": EVIDENCE_STATE,
    }


if __name__ == "__main__":
    print(health(Sample(0.98, 0.02, 3.0)))
    print(health(Sample(0.6, 0.2, 18.0)))
