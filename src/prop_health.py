#!/usr/bin/env python3
"""Propulsion health index — chamber P, mixture ratio, vibration (portfolio)."""
from __future__ import annotations
from dataclasses import dataclass
import math

SIGMA = math.e
CONFIDENCE_FLOOR = 0.31415

@dataclass
class Sample:
    chamber_p_pct: float  # 0..1 of nominal
    mr_error: float       # abs mix ratio error
    vibe_g: float

def health(s: Sample) -> dict:
    p_term = max(0.0, 1.0 - abs(s.chamber_p_pct - 1.0) * 2)
    mr_term = max(0.0, 1.0 - s.mr_error * 5)
    vibe_term = max(0.0, 1.0 - s.vibe_g / 20.0)
    idx = 0.45 * p_term + 0.35 * mr_term + 0.20 * vibe_term
    idx = max(CONFIDENCE_FLOOR, min(1.0, idx))
    if s.chamber_p_pct < 0.7 or s.vibe_g > 15:
        status = "RED"
    elif s.mr_error > 0.1 or s.vibe_g > 8:
        status = "YELLOW"
    else:
        status = "GREEN"
    return {"health": round(idx, 4), "status": status}

if __name__ == "__main__":
    print(health(Sample(0.98, 0.02, 3.0)))
    print(health(Sample(0.6, 0.2, 18.0)))
