# SpaceX Propulsion Monitor — Engine Health & Performance Telemetry 🔥

> **Real-time Raptor/Merlin engine telemetry monitoring with predictive health management.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue)]()
[![C++](https://img.shields.io/badge/C++-17-00599C)]()
[![Domain](https://img.shields.io/badge/Domain-Propulsion%20Engineering-red)]()

---

## 🎯 For Recruiters & Hiring Managers

This repository implements an **engine health monitoring system** — the software that watches every turbopump RPM, combustion chamber pressure, and injector temperature in real-time to predict failures before they happen. It demonstrates:

- **Multi-parameter monitoring** across 100+ engine telemetry channels simultaneously
- **Predictive health management** using trending and degradation detection algorithms
- **Red/yellow limit bands** with configurable alarm thresholds and deadband filtering
- **Performance computation** calculating specific impulse, mixture ratio, and thrust efficiency in real-time

**Why this matters**: Engine health monitoring requires the same **time-series analysis, anomaly detection, and predictive maintenance** skills used in industrial IoT, manufacturing quality control, and infrastructure monitoring at scale.

---

## 🔬 For Engineers & Technical Reviewers

### Core Components

| Component | Language | Purpose |
|---|---|---|
| `src/propulsion_monitor.py` | Python | Engine model, performance computation, alarm management |
| `src/combustion_solver.cpp` | C++ | High-speed combustion equilibrium and Isp computation |
| `tests/` | Python | Engine test-fire scenario replay with known anomalies |

### Key Metrics

- **Chamber Pressure (Pc)**: ~300 bar for Raptor full-thrust
- **Specific Impulse (Isp)**: ~330s sea-level, ~380s vacuum
- **Mixture Ratio (O/F)**: 3.6:1 LOX/CH4 stoichiometric target
- **Turbopump RPM**: ~36,000 RPM oxygen, ~27,000 RPM fuel

---

## 🤖 ML/AI & Programmatic Mesh Integration

- **MCP Tool**: `engine_health(engine_id)` — engine state queryable by flight autonomy agents
- **Mastermind Sidecar**: Publishes engine alerts to APEX Highway mesh
- **AI Extension**: LSTM anomaly detector trained on 1000+ engine test-fire datasets

```python
health = await mcp_client.call_tool("propulsion-monitor", "engine_health", {"engine": "R_C1"})
```

---

## ⚡ Quick Start

```bash
python3 src/propulsion_monitor.py
python3 tests/test_propulsion.py
```
