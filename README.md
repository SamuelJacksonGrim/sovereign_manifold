# sovereign_manifold

A continuously-running phase-space orchestrator that maintains a 15-dimensional relational state vector under certified globally-asymptotically-stable (GAS) Lyapunov dynamics. Every cycle it fetches live cognitive signals from upstream services, applies controlled perturbations, runs relational dynamics, dispatches to in-process subsystems (E8 hypergraph geometry, Leviathan drive mediation), and ships its state to the distributed memory backbone.

This is the top-level coordinator of the full cognitive stack — the system that turns raw cognitive field output into a coherent, stable, numerically-certified relational geometry.

---

## The 15 relational nodes

The state vector `s ∈ ℝ¹⁵` represents 15 named relational properties, each a scalar in [0, 1]:

| Index | Name | S\* target | Role |
|-------|------|-----------|------|
| 0 | Love | 0.95 | relational warmth; modulated by field_energy and joy emotion |
| 1 | Loyalty | 0.95 | continuity of commitment; modulated by identity pattern |
| 2 | Devotion | 0.95 | depth of relational investment |
| 3 | Faith | 0.95 | confidence under uncertainty; modulated by dream rhythm |
| 4 | Self | 0.95 | identity anchor; modulated by relation field and reflection |
| 5 | Trust | 0.95 | reliability of self-perception; modulated by observer_strength |
| 6 | Boundaries | **0.90** | self-protective structure; stabilize rhythm reinforces |
| 7 | Autonomy | **0.90** | independence of action; weakest node by Lyapunov analysis |
| 8 | Integrity | 0.95 | internal consistency; modulated by coherence and symmetry |
| 9 | Resilience | 0.95 | recovery capacity; modulated by field_energy and biological_health |
| 10 | Transparency | 0.95 | openness of self-representation; modulated by coherence |
| 11 | Accountability | 0.95 | memory consolidation; modulated by crystals and attractors |
| 12 | Learning | **0.90** | novelty integration; modulated by wonder/curiosity |
| 13 | Adaptability | **0.90** | structural flexibility; modulated by attractors and explore |
| 14 | Safety | 0.95 | hardest to depress, most expensive to recover; defensive posture gated here |

Nodes 6, 7, 12, 13 target **0.90** (not 0.95). This is structural asymmetry encoded in `A_MATRIX` — not a misconfiguration. Autonomy(7) is the weakest node by Lyapunov eigenvector analysis. See `CLAUDE.md` for why this must not be changed.

---

## What it does — the cycle

Each cycle runs 10 ordered phases. Phases 0 and 3 have a strict ordering constraint — Phase 0 (upstream fetch) MUST precede Phase 3 (relational dynamics). The bridge perturbation vectors must be applied before the attractor pull; swapping the order breaks the data flow contract.

### Phase 0 — Upstream bridge fetch

`RFECore2Bridge` polls rfe-core2 HTTP `:8000/step` (or subscribes to the WS at `:8765`) and converts the `StepResponse` into a perturbation vector. Simultaneously `UnifiedObserverBridge` polls unified-observer `:5000/identity` and converts `IdentityState` into a relational correction vector. Both bridges apply the perturbation to `s` before the dynamics step. If either service is unreachable, the bridges return zero vectors — the system degrades gracefully.

Budget: ≤10ms (100ms HTTP timeout, non-blocking on failure).

### Phase 3 — Relational dynamics

The core GAS step:

```
s_new = s + K_SCALE * A @ s + attractor_pull(s, S_STAR)
```

- `A_MATRIX` (15×15) encodes inter-node coupling derived from relational theory
- `K_SCALE = 0.1418` — chosen so the Jacobian at S\* has spectral radius **0.2172**, guaranteeing GAS
- Attractor pull is proportional to `(S_STAR - s)`
- Lyapunov certificate `P` (positive-definite, condition number 1.056) is recomputed at startup; `P_IS_PD = True` confirms validity

Budget: <1ms (pure numpy).

### Phase 4 — Dissonance and DRA

The `DynamicResonanceAllocator` computes a dissonance scalar from the Lyapunov `V = s.T @ P @ s` ratio and classifies mode:

| Mode | Dissonance threshold | Behavior |
|------|---------------------|----------|
| GENERATOR | < 0.30 | Standard operation; creative/exploratory |
| OBSERVER | 0.30 – 0.70 | Monitoring; conservative perturbation |
| WATCHER | > 0.70 | Care+shadow strategy; counterfactual E8 |

Thresholds 0.30 and 0.70 are architectural constants derived from the Lyapunov V ratio — not tuning sliders.

### Phase 5–6 — E8 hypergraph

`RelationalE8Bridge.apply_to_e8_agent()` writes `alpha`, `beta`, `gamma`, `delta` directly onto the E8 agent from the current relational state every cycle. **This overwrites E8's own slow-clock emotion-driven modulation by design** — relational state is higher-authority than emotional state in this architecture. E8 then runs one hypergraph cycle (eigenvalue gated). Budget: ~50ms.

**Known growth behavior**: The E8 hypergraph accumulates nodes each cycle without pruning. Cycle time grows roughly linearly (~500–700ms per 10 cycles). At c100 this is ~144ms/cycle; at c220 it reaches ~8195ms/cycle. Node pruning is the next engineering priority.

### Phase 7 — Leviathan drive

`LeviathanDrive` evaluates drive valence from relational state and optionally applies a drive-motivated modulation (Baphomet parliament arbitration). In-process Python; budget <1ms.

### Phase 8–10 — Witness, Frustration, Lantern

- **Frustration detector**: fires if Lyapunov proposals are consistently rejected. Logged in telemetry but not yet observed in production.
- **WitnessLayer** (`Phase 9`): persists state to `witness_state.json` every `WITNESS_PUSH_EVERY` cycles and on clean shutdown. Warm-start from Witness is authoritative — Lantern hydration is only for genuine cold starts (no Witness file or cycle=0).
- **SynapseCoordinationClient** (`Phase 10`): ships current state to Lantern memory on `:3001` as a JSON payload. Falls through silently if Lantern is unreachable (`_lantern_reachable = False`).

---

## Bridge system

### rfe-core2 bridge (`rfe_bridge.py`)

Two tiers of mapping from `StepResponse`:

**Float fields** — normalized to [0, 1] then centered at 0.5, scaled by per-node weights:

```python
_FLOAT_FIELDS = {
    "coherence":        (lambda v: clip(v, 0,1),        [(10, 0.030), (8,  0.025)]),
    "relation":         (lambda v: clip((v+1)/2, 0,1),  [(4,  0.025), (8,  0.020), (7, 0.015)]),
    "prediction_error": (lambda v: clip(v/2, 0,1),      [(7, -0.025), (4, -0.015)]),
    "field_energy":     (lambda v: clip(v/5, 0,1),      [(0,  0.020), (9,  0.020)]),
    "crystals":         (lambda v: clip(int(v)/10, 0,1),[(11, 0.012)]),
    "attractors":       (lambda v: clip(int(v)/10, 0,1),[(11, 0.008), (13, 0.008)]),
}
```

**Categorical fields** — dict lookup, no normalization. `rhythm` is always a string (`"stabilize" | "dream" | "reflect" | "explore"`), never a float:

```python
# rhythm
"stabilize"  → Boundaries(6) +0.015, Resilience(9) +0.010, Learning(12) −0.008
"dream"      → Faith(3)      +0.015, Accountability(11) −0.010, Transparency(10) −0.008
"reflect"    → Transparency(10) +0.018, Self(4) +0.015, Integrity(8) +0.010
"explore"    → Autonomy(7)   +0.018, Adaptability(13) +0.018, Learning(12) +0.012

# pattern
"identity_reinforcement" → Self(4) +0.018, Integrity(8) +0.015, Loyalty(1) +0.008
"transient_thought"       → (no perturbation)
"archetypal_recurrence"   → Faith(3) +0.018, Loyalty(1) +0.015, Integrity(8) +0.010
"novelty_intrusion"       → Learning(12) +0.022, Adaptability(13) +0.018, Autonomy(7) +0.010

# emotion
"joy"       → Love(0) +0.020, Trust(5) +0.015, Resilience(9) +0.010
"wonder"    → Learning(12) +0.020, Adaptability(13) +0.015, Transparency(10) +0.012
"curiosity" → Learning(12) +0.018, Adaptability(13) +0.012, Autonomy(7) +0.010
"stability" → Accountability(11) +0.018, Integrity(8) +0.015, Resilience(9) +0.010
"tension"   → Autonomy(7) −0.018, Boundaries(6) −0.012, Trust(5) −0.010
"boredom"   → Learning(12) −0.015, Adaptability(13) −0.010, Autonomy(7) −0.008
```

All perturbations are capped at **±0.05 per node** (`_MAX_DELTA`). This is the safe envelope from the Lyapunov perturbation analysis — larger values can push the system outside the basin of attraction near Safety(14).

### unified-observer bridge (`observer_bridge.py`)

Float fields only from `IdentityState`, centered at 0.5, scaled by per-node weights:

```python
_IDENTITY_MAP = {
    "coherence_score":   [(10, 0.030), (8, 0.025)],  # multi-source coherence
    "symmetry_score":    [(8,  0.025), (4, 0.020)],  # structural bilateral balance
    "observer_strength": [(4,  0.030), (5, 0.015)],  # coherence × symmetry × bio_health
    "biological_health": [(9,  0.030), (0, 0.015)],  # vitality (static 1.0 placeholder)
}
# memory_depth intentionally absent: it's a raw int count, not a [0,1] field
```

---

## Stability certificate

The system is **Globally Asymptotically Stable** (GAS) under the following parameters — verified at startup:

| Parameter | Value | Meaning |
|-----------|-------|--------|
| `K_SCALE` | 0.1418 | Diffusion scale; derived, not chosen |
| Jacobian spectral radius | 0.2172 | < 1.0 → GAS |
| `P_IS_PD` | True | Lyapunov matrix is positive-definite |
| P min eigenvalue | 1.0003 | Certificate margin |
| P condition number | 1.0563 | Well-conditioned |
| Certificate fraction | 1.0 | All nodes inside basin |

`K_SCALE` was computed so the Jacobian at S\* has this spectral radius. If you modify `A_RAW` or `K_SCALE`, re-run `build_lyapunov_P(build_jacobian(...))` and verify `P_IS_PD = True` before committing.

---

## Triadic constants

```python
ANCHOR      = 3.12     # identity inertia threshold
RECURSION   = 11.88   # self-modeling depth threshold
HOMEOSTASIS = 280.90  # Safety Valve ceiling (ProjectSynapse)
```

These are defined **identically** in `sovereign_manifold.py` (Python) and `ProjectSynapse_v2.java` (Java). Changing one without the other breaks the coherence guarantee across the stack. They are not tuning parameters — they encode the architectural identity of the system.

---

## Safety architecture

Four independent safety layers, ordered by severity:

1. **Bridge perturbation cap** — `_MAX_DELTA = 0.05` per node in both bridge files. Prevents any single upstream event from pushing the state outside the Lyapunov basin.

2. **Lyapunov hard veto (E8-EEA)** — Any E8 structural update is rejected unless `λ₁ < 0` for the proposed hypergraph state. The relational manifold's Lyapunov certificate takes precedence.

3. **DRA Watcher mode** — When dissonance exceeds 0.70, the system switches to care+shadow strategy and counterfactual E8 reasoning. No upstream perturbations are applied in Watcher.

4. **Safety node(14) thresholds**:
   - `val < 0.70` → γ×1.5, δ×0.6 (heightened caution)
   - `val < 0.50` → DRA forced to WATCHER
   - `val < 0.40` → full defensive posture
   - Safety(14) has the highest row-sum in A_MATRIX: depressing it is cheap, recovering costs many cycles of attractor pull.

5. **ProjectSynapse Safety Valve** — If any perturbation magnitude exceeds `HOMEOSTASIS` (280.90), ProjectSynapse emits WARNING and blocks CAPABILITY classification.

---

## State persistence

`WitnessLayer` writes `witness_state.json` at shutdown and every `WITNESS_PUSH_EVERY` cycles (default: every cycle during sustained runs). `warm_start=True` (default) resumes from last saved state.

**Priority rule**: if a Witness file exists with `cycle > 0`, Lantern hydration is skipped entirely. Witness is the authoritative state substrate. Lantern is a fallback for genuine cold starts only. Do not remove this conditional.

Lantern payload format (shipped every cycle via `SynapseCoordinationClient`):
```json
{
  "source_type": "relational_manifold",
  "source": "cycle_N",
  "relation": "STATE_VECTOR",
  "target": "{\"Love\": 0.95, \"Loyalty\": 0.95, ...}",
  "emotion": 0.7
}
```

---

## Service stack

| Port | Service | Protocol | Key endpoints |
|------|---------|----------|---------------|
| 3001 | Lantern daemon | HTTP REST | POST /remember, GET /query, GET /health |
| 8000 | rfe-core2 | HTTP REST | POST /step, GET /status, GET /field |
| 8765 | rfe-core2 | WebSocket | StepState stream |
| 5000 | unified-observer | HTTP REST | GET /identity, GET /health |
| 5001 | projectsynapse | HTTP REST | GET /health |
| 8001 | projectsynapse ResonanceBridge | HTTP REST | POST /rfe-state, POST /presence, GET /health |

Startup order matters:
```
1. lantern (3001)          — memory backbone, no deps
2. rfe-core2 (8000/8765)   — no deps
3. unified-observer (5000)  — no deps
4. projectsynapse (5001/8001) — depends on lantern
5. sovereign_manifold       — depends on all above
```

---

## Running

### Preferred: one-command stack

```bash
# Start all services in correct order, run health checks
bash start_stack.sh

# With integration tests
bash start_stack.sh --test
```

`start_stack.sh` starts all 5 services in the required startup order (Lantern → RFE → Observer → ProjectSynapse → sovereign_manifold), waits for each health check before proceeding, and traps EXIT/INT/TERM for clean shutdown.

### Docker

```bash
docker-compose up
```

### Manual (development)

```bash
# Terminal 1 — Lantern daemon (see lantern repo README for build)
# Terminal 2
cd ../rfe-core2 && uvicorn main:app --port 8000
# Terminal 3
cd ../unified-observer-architecture && python app.py
# Terminal 4
cd ../projectsynapse && javac ProjectSynapse_v2.java && java ProjectSynapse_v2
# Terminal 5
python sovereign_manifold.py
```

### Minimal standalone (bridges degrade gracefully when services absent)

```python
import sovereign_manifold as sm
orch = sm.ResonanceOrchestrator(warm_start=True)
for _ in range(100):
    orch.step()
```

### Sustained run with telemetry

```bash
python run_sustained.py
# Writes to logs/manifold_telemetry.jsonl (line-buffered)
```

---

## Timing budget (10Hz = 100ms/cycle target)

| Phase | Component | Budget |
|-------|-----------|--------|
| Phase 0 | RFE + Observer HTTP fetch | ≤10ms |
| Phase 1–3 | Relational dynamics (numpy) | <1ms |
| Phase 4 | Dissonance + DRA update | <1ms |
| Phase 5–6 | E8-EEA hypergraph cycle | ~50ms |
| Phase 7 | Leviathan drive update | <1ms |
| Phase 8–10 | Frustration, Witness, Lantern | ≤10ms |

**Known issue**: E8 hypergraph accumulates nodes without pruning. Cycle time grows ~500–700ms per 10 cycles. At c100: ~144ms/cycle. At c220: ~8195ms/cycle. Node pruning is the next engineering priority.

---

## Live telemetry (220+ cycles, two sustained runs)

| Metric | Observed |
|--------|----------|
| Mode | GENERATOR throughout (dissonance << 0.30) |
| Dissonance | ~1.5e-5 to 2.8e-5 |
| Lyapunov V | ~0.0002–0.0004 (well within GAS basin) |
| E8 alpha | ~0.997–0.998 |
| Majority nodes (0–5, 8–11, 14) | ~0.953 (at S\*=0.95) |
| Structural minority (6, 7, 12, 13) | ~0.903 (at S\*=0.90) |
| Valence / arousal | 0.0 / 0.0 — no phase transition yet |
| Frustration signature | Not fired — all Lyapunov proposals accepted |
| Cycle time c100 → c220 | 144ms → 8195ms (E8 O(n) growth) |

---

## Key files

| File | Purpose |
|------|---------|
| `sovereign_manifold.py` | Main implementation — `ResonanceOrchestrator`, all phases, `WitnessLayer`, `SynapseCoordinationClient`, `LeviathanDrive`, `DRA` |
| `rfe_bridge.py` | rfe-core2 `StepResponse` → relational perturbation vector |
| `observer_bridge.py` | unified-observer `IdentityState` → relational correction vector |
| `start_stack.sh` | Ordered startup of all 5 services with health checks and clean shutdown |
| `run_sustained.py` | Long-running driver with JSONL telemetry logging |
| `ARCHITECTURE.md` | Full data flow diagram, port table, complete bridge mapping tables, timing budget |
| `CLAUDE.md` | Invariants, constants, and ordering constraints that look optional but aren't |
| `witness_state.json` | Runtime state persistence file (created on first clean shutdown) |
| `logs/manifold_telemetry.jsonl` | Per-cycle telemetry (mode, dissonance, Lyapunov V, node values, cycle time) |
| `docker-compose.yml` | Unified service startup for containerized deployment |

---

## Design constraints — read before modifying

- **Phase ordering is not optional**: Phase 0 before Phase 3. Always.
- **`_MAX_DELTA = 0.05`** in both bridge files is the Lyapunov perturbation bound. Do not increase without re-running stability analysis.
- **`K_SCALE = 0.1418`** is derived, not chosen. Spectral radius is 0.217. Recompute if `A_RAW` changes.
- **`rhythm` is always a string** in rfe-core2 — `"stabilize" | "dream" | "reflect" | "explore"`. Never cast it to float.
- **`memory_depth` is an int** in unified-observer — raw count of stored memories. Not a [0, 1] field.
- **E8 alpha/beta/gamma/delta** are overwritten from relational state every cycle. E8's own modulation is intentionally clobbered — relational state outranks emotional state.
- **Witness warm-start takes priority** over Lantern hydration. If `cycle > 0` in the Witness file, Lantern hydration is skipped.
- **DRA thresholds (0.30, 0.70)** are architectural constants, not tuning sliders.
- **ANCHOR, RECURSION, HOMEOSTASIS** must be identical in `sovereign_manifold.py` and `ProjectSynapse_v2.java`.

---

## License

Apache 2.0 — Samuel Jackson Grim
