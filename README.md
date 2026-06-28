# SpaceX Propulsion Monitor

Raptor engine health monitoring and multi-engine controller for Falcon 9 / Starship.

## Architecture

**Double Helix (Alpha + Omega)**

- **Alpha** (`src/alpha/raptor_health.py`): Statistical health analysis — moving windows, anomaly detection, threshold monitoring.
- **Omega** (`src/omega/engine_controller.py`): Engine state machine — startup, throttle, shutdown, emergency stop, engine-out capability.

## Features

- 8 sensor types (chamber pressure, turbopump speed, temps, vibration, thrust)
- Statistical anomaly detection (3-sigma outliers, rate-of-change)
- 3-tier health states (NOMINAL, DEGRADED, CRITICAL)
- Multi-engine coordination (9 for F9, 33 for Starship)
- Throttle profile management
- Engine-out graceful degradation
- Zero external dependencies
