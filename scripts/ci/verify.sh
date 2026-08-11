#!/usr/bin/env bash
set -euo pipefail

python -m pip install --disable-pip-version-check --quiet 'pytest==9.1.1'
python -m compileall -q src tests scripts mastermind_sidecar.py
python -m pytest -q tests
python scripts/operate.py
python scripts/verify_public_surface.py
