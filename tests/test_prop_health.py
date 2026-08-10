"""Tests drive shipped prop_health.health — no magic ANSWER constants."""
from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from prop_health import Sample, health  # noqa: E402


class PropHealthTests(unittest.TestCase):
    def test_green_nominal_sample(self) -> None:
        r = health(Sample(1.0, 0.01, 2.0))
        self.assertEqual(r["status"], "GREEN")
        self.assertGreater(r["health"], 0.9)

    def test_red_off_nominal_sample(self) -> None:
        r = health(Sample(0.5, 0.0, 1.0))
        self.assertEqual(r["status"], "RED")
        self.assertLess(r["health"], 0.8)


if __name__ == "__main__":
    unittest.main()
