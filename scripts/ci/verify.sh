#!/usr/bin/env bash
set -euo pipefail

python -m pip install --disable-pip-version-check --quiet 'pytest==9.1.1' 'setuptools>=75' wheel
python -m compileall -q src tests scripts mastermind_sidecar.py
python -m pytest -q tests
rm -rf dist build *.egg-info src/*.egg-info
python -m pip wheel . --no-deps --no-build-isolation -w dist
python -m pip install --disable-pip-version-check --quiet --force-reinstall dist/*.whl
health-lab-demo --compact > /tmp/health-lab-demo.json
python - <<'PY'
import json
from pathlib import Path
receipt = json.loads(Path('/tmp/health-lab-demo.json').read_text())
assert receipt['evidence_state'] == 'LOCAL_PROPULSION_HEALTH_SIMULATION_NOT_FLIGHT_ENGINE_AUTHORITY'
assert receipt['multi_sensor']['anomaly']['severity'] == 'CRITICAL'
assert receipt['simulated_control']['emergency_action'] == 'SIMULATED_EMERGENCY_STOP'
assert receipt['external_actions_executed'] == 0
assert len(receipt['digest']) == 64
PY
python scripts/operate.py
python scripts/verify_public_surface.py
python - <<'PY'
import json
from pathlib import Path
caps = json.loads(Path('machine/crystallization/capability-manifest.json').read_text())
gaps = json.loads(Path('machine/crystallization/gap-matrix.json').read_text())
assert caps['capabilities']
assert all(item['state'] == 'WORKING' for item in caps['capabilities'])
assert gaps['gaps'] == []
PY
