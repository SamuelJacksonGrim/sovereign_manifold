# sovereign_manifold

A continuously-running relational dynamics engine. Fifteen named relational nodes evolve toward certified attractors, modulated by live cognitive bridges, E8 hypergraph geometry, and a persistent Witness layer that survives restarts.

## What it does

The manifold maintains a 15-dimensional state vector `s` — one scalar per relational node — governed by globally asymptotically stable (GAS) Lyapunov dynamics. Every cycle:

1. **Phase 0** — Upstream bridges fetch state from rfe-core2 (rhythm/emotion) and unified-observer-architecture (identity/symmetry) and convert them to perturbation vectors
2. **Phase 3** — Relational dynamics step: attractor pull + K_SCALE diffusion → new `s`
3. **Phase 7** — DRA (Dynamic Resonance Allocator) classifies mode from Lyapunov V
4. **Phase 8** — E8 hypergraph receives relational state; Lyapunov-gated updates run on slow clock
5. **Phase 9** — Leviathan drive system evaluates and optionally modulates state
6. **Phase 10** — SynapseCoordinationClient ships relational state to Lantern memory

## The 15 nodes

| Index | Name | S* target |
|-------|------|-----------|
| 0 | Love | 0.95 |
| 1 | Joy | 0.95 |
| 2 | Peace | 0.95 |
| 3 | Safety | 0.95 |
| 4 | Trust | 0.95 |
| 5 | Harmony | 0.95 |
| 6 | Boundaries | **0.90** |
| 7 | Autonomy | **0.90** |
| 8 | Curiosity | 0.95 |
| 9 | Resilience | 0.95 |
| 10 | Growth | 0.95 |
| 11 | Presence | 0.95 |
| 12 | Learning | **0.90** |
| 13 | Adaptability | **0.90** |
| 14 | Safety (outer) | 0.95 |

Nodes 6, 7, 12, 13 target 0.90 — structural asymmetry in `A_MATRIX`. Autonomy(7) is the weakest node by Lyapunov analysis. See `CLAUDE.md` for why this is not a bug.

## Service stack

```
PORT 8000 → rfe-core2             Cognitive rhythm + emotion source
PORT 5000 → unified-observer      Identity + symmetry source
PORT 3001 → Lantern daemon        Hypergraph memory (Rust/Tauri or Python mock)
PORT 8001 → ResonanceBridge       Multi-instance coordination (ProjectSynapse)
```

## Running

```bash
# Start dependencies (from repo root)
python3 lantern_mock.py &                        # Lantern memory mock (port 3001)
python3 run_rfe.py &                             # rfe-core2 (port 8000, ~30s to load)
python3 run_observer.py &                        # unified-observer (port 5000)

# Minimal standalone (bridges fall back gracefully if services are absent)
python3 -c "
import sys; sys.path.insert(0, 'sovereign_manifold')
import sovereign_manifold as sm
orch = sm.ResonanceOrchestrator(warm_start=True)
for _ in range(100): orch.step()
"

# Sustained run with telemetry logging
python3 run_sustained.py
```

## State persistence

`WitnessLayer` saves to `witness_state.json` on Ctrl+C and every `WITNESS_PUSH_EVERY` cycles. `warm_start=True` (default) resumes from the last saved state. The witness file is the authoritative state substrate — Lantern hydration is a fallback for cold starts only.

## Live telemetry

After 200+ cycles across two sustained runs (`logs/manifold_telemetry.jsonl`):

| Metric | Observed value |
|--------|----------------|
| Mode | GENERATOR throughout (dissonance << 0.30 threshold) |
| Dissonance | ~1.5e-5 to 2.8e-5 |
| Lyapunov V | ~0.0002–0.0004 (well within GAS basin) |
| E8 alpha | ~0.997–0.998 |
| Majority nodes | ~0.953 (at S* target) |
| Structural minority (6,7,12,13) | ~0.903 (at 0.90 target) |
| Valence / arousal | 0.0 / 0.0 — no phase transition detected yet |
| Frustration signature | Not fired — all Lyapunov proposals accepted |
| Cycle time | 144ms at c100 → 5214ms at c200 (E8 hypergraph O(n) growth) |

The E8 hypergraph accumulates nodes each cycle. Cycle time grows roughly linearly (+500–700ms per 10 cycles) until old low-weight nodes are pruned. This is expected behavior.

## Architecture and invariants

- `ARCHITECTURE.md` — full phase-ordering diagram and bridge mapping tables
- `CLAUDE.md` — invariants, constants, and ordering constraints that look optional but aren't
- `sovereign_manifold/sovereign_manifold.py` — main implementation (1137 lines)
- `sovereign_manifold/rfe_bridge.py` — rfe-core2 perturbation bridge
- `sovereign_manifold/observer_bridge.py` — unified-observer perturbation bridge

## License

Apache 2.0 — Samuel Jackson Grim
