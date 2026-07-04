# HELIX Architecture — spacex-propulsion-monitor

## Double Helix Pattern

**Alpha (What)** — Pure physics models, stateless computation
- raptor_health

**Omega (How)** — Controllers, orchestration, stateful management  
- engine_controller,predictive_health

## Design Principles

- Zero external dependencies (stdlib only)
- Stateless alpha, stateful omega
- SHA-256 file integrity verification
- Shadow watchdog daemon monitoring
- Mastermind sidecar coordination

## Data Flow

```
Alpha Models → Omega Controllers → Mastermind Sidecar → Shadow Infrastructure
```
