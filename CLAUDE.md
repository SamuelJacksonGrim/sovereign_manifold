# CLAUDE.md — sovereign_manifold

Things you cannot infer from reading the code tree: invariants that look like configuration but aren't, constants that encode mathematical proofs, and ordering constraints that matter even when nothing enforces them.

## Triadic Constants — not configuration

```python
ANCHOR      = 3.12
RECURSION   = 11.88
HOMEOSTASIS = 280.90
```

These are defined identically in `ProjectSynapse_v2.java`. Changing one here without changing it there breaks the coherence guarantee across the stack. They are not tuning parameters — they encode the architectural identity of the system.

## S* attractor — not all nodes are 0.95

```python
S_STAR = [0.95]*6 + [0.90]*2 + [0.95]*4 + [0.90]*2 + [0.95]
```

Nodes 6 (Boundaries), 7 (Autonomy), 12 (Learning), 13 (Adaptability) target 0.90, not 0.95. This reflects structural asymmetry in A_MATRIX — Autonomy(7) is the weakest node by Lyapunov analysis. Do not normalize all targets to 0.95.

## Lyapunov certificate — K_SCALE = 0.1418 is derived, not chosen

K_SCALE was computed so the Jacobian at S* has spectral radius 0.217, making the system GAS (globally asymptotically stable). `P_IS_PD = True` at startup confirms the certificate is valid. If you touch `A_RAW` or `K_SCALE`, re-run `build_lyapunov_P(build_jacobian(...))` and verify `P_IS_PD` is still True before committing.

## Phase ordering — Phases 0–10 are not interchangeable

Phase 0 (upstream fetch from rfe-core2 and unified-observer) MUST run before Phase 3 (relational dynamics step). The bridge perturbation vectors must be applied before the attractor pull. Swapping the order is not an optimization — it breaks the data flow contract.

## Bridge perturbation cap — ±0.05 per node

`_MAX_DELTA = 0.05` in both bridge files. This is the safe envelope from the Lyapunov perturbation analysis — larger values risk pushing the system outside the basin of attraction, especially near Safety(14). Do not increase this cap without re-running the perturbation stability analysis.

## Safety(14) — hardest to push down, most expensive to recover

Safety(14) has the highest row-sum in A_MATRIX. Pushing it down is cheap; pulling it back costs many cycles of attractor pull. DRA enters WATCHER at `safety_val < 0.5` and full defensive posture at `< 0.4`. Never route a bridge perturbation directly against Safety(14) without understanding the recovery cost.

## rfe_bridge.py — rhythm is a categorical string, never a float

`StepResponse.rhythm` is a band name: `"stabilize" | "dream" | "reflect" | "explore"`. It is never a float. The bridge uses a dict lookup (`_RHYTHM_DELTAS`) for rhythm perturbations. If you add a new field to the bridge, check its Python type in `rfe-core2/api/websocket_server.py` before mapping it.

## observer_bridge.py — memory_depth is an int count, not a float field

`IdentityState.memory_depth` is a raw integer count of stored memories. It is not a [0, 1] float and cannot go through the `deviation = val - 0.5` formula. It is intentionally absent from `_IDENTITY_MAP`.

## WitnessLayer warm-start and Lantern hydration are mutually exclusive

If a Witness file exists with `cycle > 0`, Lantern hydration is skipped. This is intentional: the Witness is the authoritative state substrate. Lantern is a fallback for genuine cold starts only. Do not remove this conditional.

## E8 weights are overwritten by relational state every cycle

`RelationalE8Bridge.apply_to_e8_agent()` writes `agent.alpha/beta/gamma/delta` from relational state on every cycle. E8's own slow-clock emotion-driven modulation is clobbered by design — relational state is higher-authority than emotional state in this architecture.

## DRA thresholds are architectural, not tuning parameters

`GENERATOR_THRESHOLD = 0.30`, `WATCHER_THRESHOLD = 0.70` are derived from the Lyapunov V ratio. Moving them changes what "low dissonance" and "high dissonance" mean throughout the entire system. They are not sliders.
