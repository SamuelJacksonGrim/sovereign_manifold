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

Handled by `rfe_bridge.py` (`RFECore2Bridge.fetch_perturbation`).

**Float fields** — normalized to [0, 1], centered at 0.5, then scaled:

```
coherence        → Transparency(10) +0.030/unit, Integrity(8)  +0.025/unit
                   [Watcher composite; range [0,1]; high = internally consistent]

relation         → Self(4) +0.025/unit, Integrity(8) +0.020/unit, Autonomy(7) +0.015/unit
                   [Witness composite; range [-1,1] mapped to [0,1];
                    high = strong identity continuity across timescales]

prediction_error → Autonomy(7) −0.025/unit, Self(4) −0.015/unit
                   [L2 distance predicted→actual; normalized /2.0;
                    high = system surprised itself]

field_energy     → Love(0) +0.020/unit, Resilience(9) +0.020/unit
                   [L2 norm of resonance field; normalized /5.0;
                    high = cognitive vitality, aliveness]

crystals (int)   → Accountability(11) +0.012/unit
                   [count normalized /10; memory consolidation]

attractors (int) → Accountability(11) +0.008/unit, Adaptability(13) +0.008/unit
                   [count normalized /10; richer cognitive landscape]
```

**Categorical fields** — direct delta lookup, no normalization:

```
rhythm "stabilize"  → Boundaries(6) +0.015, Resilience(9) +0.010, Learning(12) −0.008
rhythm "dream"      → Faith(3) +0.015, Accountability(11) −0.010, Transparency(10) −0.008
rhythm "reflect"    → Transparency(10) +0.018, Self(4) +0.015, Integrity(8) +0.010
rhythm "explore"    → Autonomy(7) +0.018, Adaptability(13) +0.018, Learning(12) +0.012

pattern "identity_reinforcement" → Self(4) +0.018, Integrity(8) +0.015, Loyalty(1) +0.008
pattern "transient_thought"       → (no perturbation)
pattern "archetypal_recurrence"   → Faith(3) +0.018, Loyalty(1) +0.015, Integrity(8) +0.010
pattern "novelty_intrusion"       → Learning(12) +0.022, Adaptability(13) +0.018, Autonomy(7) +0.010

emotion "joy"       → Love(0) +0.020, Trust(5) +0.015, Resilience(9) +0.010
emotion "wonder"    → Learning(12) +0.020, Adaptability(13) +0.015, Transparency(10) +0.012
emotion "curiosity" → Learning(12) +0.018, Adaptability(13) +0.012, Autonomy(7) +0.010
emotion "stability" → Accountability(11) +0.018, Integrity(8) +0.015, Resilience(9) +0.010
emotion "tension"   → Autonomy(7) −0.018, Boundaries(6) −0.012, Trust(5) −0.010
emotion "boredom"   → Learning(12) −0.015, Adaptability(13) −0.010, Autonomy(7) −0.008
```

All perturbations capped at ±0.05 per node.

### unified-observer IdentityState → Relational Correction

Handled by `observer_bridge.py` (`UnifiedObserverBridge.fetch_relational_correction`):

```
coherence_score   → Transparency(10) +0.030/unit, Integrity(8)   +0.025/unit
                    [multi-source coherence: Resting/Circuit/Temporal average]

symmetry_score    → Integrity(8) +0.025/unit, Self(4) +0.020/unit
                    [structural bilateral balance — NOT emotional;
                     maps to structural wholeness and identity anchor]

observer_strength → Self(4) +0.030/unit, Trust(5) +0.015/unit
                    [multiplicative: coherence × symmetry × bio_health;
                     strong observer enables trusting one's own perception]

biological_health → Resilience(9) +0.030/unit, Love(0) +0.015/unit
                    [vitality (currently static placeholder at 1.0);
                     physical health supports resilience and relational warmth]
```

**Note on memory_depth**: `IdentityState.memory_depth` is an `int` count of stored
memories. It is not a [0, 1] float and cannot be mapped through the centering formula.
It is intentionally absent from `_IDENTITY_MAP`.

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
| `sovereign_manifold.py` | sovereign_manifold | Phase 0 (upstream fetch), bridge init, Lantern hydration |
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
