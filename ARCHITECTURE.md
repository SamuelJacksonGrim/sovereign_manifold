# Architecture: The Connected Stack

## Data Flow

```
[scraper-framework]            optional external world input
        ↓ JSON events
[rfe-core2 :8000/:8765]        cognitive field inference (tokens → attractors → emotion)
        ↓ StepResponse → perturbation vector
[unified-observer :5000]       identity observation (coherence, symmetry, circadian)
        ↓ IdentityState → relational corrections
[sovereign_manifold]           10Hz phase-space orchestrator
   ├── [e8-eea]                 emotional intelligence (in-process Python)
   ├── [leviathan]              drive mediation (in-process Python)
   ├── [projectsynapse :5001/:8001]  Java world model + vector fork safety
   └── [lantern :3001]          Rust temporal memory backbone (run on host)
```

## Port Table

| Service | Port | Protocol | Key Endpoints |
|---|---|---|---|
| lantern | 3001 | HTTP REST | POST /remember, GET /query, GET /health |
| rfe-core2 | 8000 | HTTP REST | POST /step, GET /status, GET /field |
| rfe-core2 | 8765 | WebSocket | StepState stream |
| unified-observer | 5000 | HTTP REST | GET /identity, GET /health |
| projectsynapse | 5001 | HTTP REST | GET /health |
| projectsynapse (ResonanceBridge) | 8001 | HTTP REST | POST /rfe-state, POST /presence, GET /health |

## Triadic Constants (shared across all layers)

```
ANCHOR      = 3.12    identity inertia threshold
RECURSION   = 11.88   self-modeling depth threshold
HOMEOSTASIS = 280.90  stability under perturbation (Safety Valve ceiling)
```

Defined identically in:
- `sovereign_manifold.py` (Python)
- `ProjectSynapse_v2.java` (Java)
- Referenced in: Lyapunov safety analysis, WorldModel ANCHOR/10 prune threshold, vector fork Safety Valve

## Node Index Reference (Relational ℛ^15)

```
 0 Love          1 Loyalty       2 Devotion      3 Faith
 4 Self          5 Trust         6 Boundaries    7 Autonomy
 8 Integrity     9 Resilience   10 Transparency  11 Accountability
12 Learning     13 Adaptability  14 Safety
```

## Data Type Mappings

### rfe-core2 StepResponse → Relational Perturbation

Handled by `rfe_bridge.py` (`RFECore2Bridge.fetch_perturbation`):

```
coherence        → Transparency(10) +0.03/unit,  Integrity(8)  +0.02/unit
rhythm           → Resilience(9)    +0.03/unit
prediction_error → Autonomy(7)      −0.025/unit, Self(4)       −0.015/unit
field_energy     → Love(0)          +0.02/unit,  Self(4)       +0.02/unit
```

All perturbations centered at 0.5, capped at ±0.05 per node.

### unified-observer IdentityState → Relational Correction

Handled by `observer_bridge.py` (`UnifiedObserverBridge.fetch_relational_correction`):

```
coherence_score   → Transparency(10) +0.030/unit, Integrity(8)   +0.025/unit
symmetry_score    → Faith(3)         +0.025/unit, Love(0)        +0.020/unit
observer_strength → Self(4)          +0.030/unit
memory_depth      → Learning(12)     +0.025/unit, Resilience(9)  +0.020/unit
biological_health → Resilience(9)    +0.030/unit
```

**Note**: The observer endpoint is assumed to be `GET /identity`. Adjust
`UnifiedObserverBridge.__init__(endpoint=...)` if the actual unified-observer
API uses a different path.

### sovereign_manifold → Lantern (existing)

```json
{"source_type": "relational_manifold", "source": "cycle_N",
 "relation": "STATE_VECTOR", "target": "{\"Love\": 0.95, ...}", "emotion": 0.7}
```

### rfe-core2 → projectsynapse ResonanceBridge

`POST http://localhost:8001/rfe-state`:
```json
{"coherence": 0.8, "rhythm": 0.7, "prediction_error": 0.2, "field_energy": 0.9}
```
Maps to `WorldModel.update("RFE_COHERENCE", coherence)` etc.

## Integration Files Added

| File | Repo | Purpose |
|---|---|---|
| `rfe_bridge.py` | sovereign_manifold | RFE-Core2 → relational perturbation |
| `observer_bridge.py` | sovereign_manifold | Unified Observer → relational correction |
| `docker-compose.yml` | sovereign_manifold | Unified service startup |
| `Dockerfile` | sovereign_manifold | Container for sovereign_manifold |
| `requirements.txt` | sovereign_manifold | Python deps |
| `ARCHITECTURE.md` | sovereign_manifold | This document |
| `Dockerfile` | projectsynapse | Container for ProjectSynapse_v2 |

Modified files:

| File | Repo | Changes |
|---|---|---|
| `sovereign_manifold.py` | sovereign_manifold | Phase 0 (upstream fetch), bridge init |
| `ProjectSynapse_v2.java` | projectsynapse | HTTP server on :8001, /rfe-state + /health handlers |

## Startup Sequence

```
1. lantern (port 3001)         — memory backbone, no service deps
2. rfe-core2 (port 8000/8765)  — no service deps
3. unified-observer (port 5000) — no service deps
4. projectsynapse (5001/8001)   — depends on lantern
5. sovereign_manifold           — depends on all above
```

With Docker:
```bash
# From the sovereign_manifold directory
docker-compose up
```

Without Docker (dev):
```bash
# Terminal 1: lantern daemon (see lantern repo README)
# Terminal 2:
cd ../rfe-core2 && uvicorn main:app --port 8000
# Terminal 3:
cd ../unified-observer-architecture && python app.py
# Terminal 4:
cd ../projectsynapse && javac ProjectSynapse_v2.java && java ProjectSynapse_v2
# Terminal 5:
python sovereign_manifold.py
```

## Repos Needing Dockerfiles

- **rfe-core2**: needs `Dockerfile` — FastAPI, so: `FROM python:3.11-slim`, install deps, `uvicorn main:app --host 0.0.0.0 --port 8000`
- **unified-observer-architecture**: already has `docker-compose.yml`, check for `Dockerfile`
- **projectsynapse**: `Dockerfile` added in this integration pass

## Timing Budget (10Hz = 100ms/cycle)

| Phase | Component | Budget |
|---|---|---|
| Phase 0 | RFE + Observer HTTP fetch | ≤10ms (100ms timeout, non-blocking on failure) |
| Phase 1–3 | Relational dynamics (numpy) | <1ms |
| Phase 4 | Dissonance + DRA update | <1ms |
| Phase 5–6 | E8-EEA cycle | ~50ms |
| Phase 7 | Leviathan drive update | <1ms |
| Phase 8–10 | Frustration, Witness, Lantern | ≤10ms async |

## Safety Architecture (unchanged)

1. **Lyapunov hard veto** (E8-EEA): λ₁ < 0 required for any structural update
2. **DRA Watcher mode**: dissonance > 0.7 forces care+shadow, counterfactual E8 strategy
3. **Safety node (14)**: val < 0.7 → γ×1.5, δ×0.6; val < 0.4 → full defensive posture
4. **ProjectSynapse Safety Valve**: perturbation > HOMEOSTASIS (280.90) → WARNING only, never CAPABILITY
