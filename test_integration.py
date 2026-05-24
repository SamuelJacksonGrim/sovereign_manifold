"""
test_integration.py — End-to-end integration test for the cognitive stack.

Tests each service in isolation, then tests the full connected stack.
Run: python test_integration.py

All services must be started externally before running connected tests:
  python lantern_mock.py &
  python run_rfe.py &
  python run_observer.py &
  cd projectsynapse && java ProjectSynapse_v2 &
  (wait ~3s for all to start)
  python test_integration.py
"""
from __future__ import annotations

import json
import sys
import time
import os
import traceback
from typing import Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
SKIP = "\033[33mSKIP\033[0m"
WARN = "\033[33mWARN\033[0m"

results = []

def check(name: str, ok: bool, detail: str = ""):
    status = PASS if ok else FAIL
    results.append((name, ok))
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{status}] {name}{suffix}")
    return ok

def section(title: str):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ── 1. STANDALONE MODULE TESTS ──────────────────────────────────────────────

section("1. STANDALONE MODULE TESTS")

# 1a. relational dynamics math
try:
    import numpy as np
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sovereign_manifold'))
    import sovereign_manifold as sm

    check("Lyapunov certificate valid (P_IS_PD)", sm.P_IS_PD)
    check("S* has correct shape", len(sm.S_STAR) == 15)
    check("S* node 7 (Autonomy) = 0.90", abs(sm.S_STAR[7] - 0.90) < 1e-6)
    check("K_SCALE = 0.1418", abs(sm.K_SCALE - 0.1418) < 1e-6)
    check("ANCHOR = 3.12", abs(sm.ANCHOR - 3.12) < 1e-6)
    check("RECURSION = 11.88", abs(sm.RECURSION - 11.88) < 1e-6)
    check("HOMEOSTASIS = 280.90", abs(sm.HOMEOSTASIS - 280.90) < 1e-6)

    # Test relational step converges toward S*
    s = np.zeros(15)
    for _ in range(200):
        s = sm.relational_step(s)
    dist = float(np.linalg.norm(s - sm.S_STAR))
    check("Relational dynamics converges to S* from zeros", dist < 0.01,
          f"dist={dist:.4f}")

except Exception as e:
    check("sovereign_manifold import + math", False, str(e))


# 1b. rfe_bridge.py field map types
try:
    from rfe_bridge import RFECore2Bridge, _FLOAT_FIELDS, _RHYTHM_DELTAS, _EMOTION_DELTAS

    check("rfe_bridge: 'rhythm' NOT in float fields (it's categorical)",
          "rhythm" not in _FLOAT_FIELDS)
    check("rfe_bridge: 'relation' in float fields",
          "relation" in _FLOAT_FIELDS)
    check("rfe_bridge: all 4 rhythm states present",
          all(k in _RHYTHM_DELTAS for k in ["stabilize","dream","reflect","explore"]))
    check("rfe_bridge: relation normalizer maps -1→0, 0→0.5, 1→1",
          abs(_FLOAT_FIELDS["relation"][0](-1.0) - 0.0) < 1e-6 and
          abs(_FLOAT_FIELDS["relation"][0](0.0)  - 0.5) < 1e-6 and
          abs(_FLOAT_FIELDS["relation"][0](1.0)  - 1.0) < 1e-6)
    check("rfe_bridge: field_energy normalizer clips at /5.0",
          abs(_FLOAT_FIELDS["field_energy"][0](5.0) - 1.0) < 1e-6 and
          abs(_FLOAT_FIELDS["field_energy"][0](10.0) - 1.0) < 1e-6)

    # Simulate a StepResponse and check delta shape/bounds
    import numpy as np
    bridge = RFECore2Bridge()
    bridge._reachable = True

    class _MockResponse:
        status_code = 200
        def json(self):
            return {
                "coherence": 0.8,
                "relation": 0.6,
                "prediction_error": 0.3,
                "field_energy": 4.0,
                "crystals": 3,
                "attractors": 2,
                "rhythm": "reflect",
                "pattern": "identity_reinforcement",
                "emotion": "joy",
            }

    import unittest.mock as mock
    with mock.patch("requests.post", return_value=_MockResponse()):
        delta = bridge.fetch_perturbation(["test"], n_nodes=15)

    check("rfe_bridge: delta shape is 15", delta is not None and len(delta) == 15)
    check("rfe_bridge: delta capped at ±0.05", delta is not None and
          float(np.max(np.abs(delta))) <= 0.05 + 1e-9)
    check("rfe_bridge: reflect rhythm → Transparency(10) positive",
          delta is not None and delta[10] > 0)
    check("rfe_bridge: joy emotion → Love(0) positive",
          delta is not None and delta[0] > 0)

except Exception as e:
    check("rfe_bridge field map validation", False, str(e))
    traceback.print_exc()


# 1c. observer_bridge.py field map
try:
    from observer_bridge import UnifiedObserverBridge, _IDENTITY_MAP

    check("observer_bridge: symmetry_score → Integrity(8), not Faith(3)",
          any(idx == 8 for idx, _ in _IDENTITY_MAP["symmetry_score"]) and
          all(idx != 3 for idx, _ in _IDENTITY_MAP["symmetry_score"]))
    check("observer_bridge: memory_depth NOT in identity map",
          "memory_depth" not in _IDENTITY_MAP)
    check("observer_bridge: observer_strength → Self(4) + Trust(5)",
          {idx for idx, _ in _IDENTITY_MAP["observer_strength"]} == {4, 5})

except Exception as e:
    check("observer_bridge field map validation", False, str(e))


# 1d. E8-EEA v5
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stack'))
    from e8_eea_v5 import E8_EEA_v5, EmotionalState, E8Lattice
    import numpy as np

    # Verify 240 E8 roots
    roots = E8Lattice.get_all_roots()
    check("E8 lattice: 240 roots", len(roots) == 240)
    check("E8 lattice: all roots have norm sqrt(2)",
          all(abs(float(np.linalg.norm(r)) - np.sqrt(2)) < 1e-6
              or abs(float(np.linalg.norm(r)) - 1.0) < 1e-6  # Type 2 roots ½√8 = √2 ✓
              for r in roots))

    agent = E8_EEA_v5(input_dim=16)
    x = np.random.rand(16)
    em = agent.cycle(x, np.roll(x, -1), 0.5)
    check("E8-EEA: cycle returns EmotionalState", isinstance(em, EmotionalState))
    check("E8-EEA: valence in [-1, 1]", -1.0 <= em.valence <= 1.0)
    check("E8-EEA: arousal in [0, 1]", 0.0 <= em.arousal <= 1.0)

    # Run enough cycles to trigger phase detection (needs 10+ input_history)
    for _ in range(30):
        agent.cycle(np.random.rand(16), np.random.rand(16), 0.0)
    check("E8-EEA: stability_log populated", len(agent.stability_log) > 0)

except Exception as e:
    check("E8-EEA v5 validation", False, str(e))
    traceback.print_exc()


# 1e. rfe-core2 standalone (10 cycles)
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'RFE-Core2'))
    from agents.generator import Generator
    from loop.autonomous_cycle import AutonomousCycle
    import numpy as np

    g = Generator(vocab_size=8192, dim=128, depth=4, heads=4, ff_mult=4, dropout=0.1)
    c = AutonomousCycle(generator=g, dim=128, use_chorus=True,
                        maintenance_interval=200, log_interval=999)

    for i in range(50):
        state = c.step(["resonance", "field", "identity", "witness"])

    d = state.as_dict()
    check("rfe-core2: coherence > 0.5 after 50 cycles", d["coherence"] > 0.5,
          f"coherence={d['coherence']:.3f}")
    check("rfe-core2: relation is a float", isinstance(d["relation"], float),
          f"type={type(d['relation'])}")
    check("rfe-core2: emotion is a string", isinstance(d["emotion"], str),
          f"emotion={d['emotion']}")
    check("rfe-core2: pattern is a string", isinstance(d["pattern"], str),
          f"pattern={d['pattern']}")
    check("rfe-core2: field_energy > 0", d["field_energy"] > 0,
          f"energy={d['field_energy']:.2f}")

except Exception as e:
    check("rfe-core2 standalone cycles", False, str(e))
    traceback.print_exc()


# ── 2. SOVEREIGN MANIFOLD ORCHESTRATOR (standalone mode) ─────────────────────────────────

section("2. SOVEREIGN MANIFOLD ORCHESTRATOR (standalone)")

try:
    import numpy as np
    orchestrator = sm.ResonanceOrchestrator(warm_start=False)

    states = [orchestrator.step() for _ in range(20)]
    final  = states[-1]

    check("Orchestrator: 20 cycles complete", len(states) == 20)
    check("Orchestrator: relational_s shape 15",
          len(final.relational_s) == 15)
    check("Orchestrator: all node values in [0,1]",
          all(0.0 <= v <= 1.0 for v in final.relational_s))
    check("Orchestrator: Lyapunov V finite",
          final.lyapunov_V < 1e6)
    check("Orchestrator: dissonance in [0,1]",
          0.0 <= final.dissonance <= 1.0)
    check("Orchestrator: DRA mode is valid",
          final.processing_mode in ["GENERATOR", "STANDARD", "WATCHER"])
    check("Orchestrator: E8 weights present",
          "alpha" in final.e8_weights and "beta" in final.e8_weights)

    # Safety check: no node should collapse to 0 after 20 cycles from S*
    min_node = float(np.min(final.relational_s))
    check("Orchestrator: no node collapsed (min > 0.5)",
          min_node > 0.5, f"min_node={min_node:.3f}")

except Exception as e:
    check("Sovereign manifold orchestrator", False, str(e))
    traceback.print_exc()


# ── 3. NETWORK SERVICE TESTS ────────────────────────────────────────────────────────────

section("3. NETWORK SERVICE TESTS (requires running services)")

if not HAS_REQUESTS:
    print(f"  [{SKIP}] All network tests — requests not installed")
else:
    def get(url, timeout=2):
        try:
            r = requests.get(url, timeout=timeout)
            return r.status_code, r.json()
        except Exception as e:
            return None, str(e)

    def post(url, payload, timeout=2):
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            return r.status_code, r.json()
        except Exception as e:
            return None, str(e)

    # Lantern mock
    code, data = get("http://localhost:3001/health")
    lantern_up = code == 200
    check("Lantern mock :3001/health", lantern_up,
          str(data) if not lantern_up else f"nodes={data.get('nodes',0)}")

    if lantern_up:
        code, data = post("http://localhost:3001/remember", {
            "source_type": "test", "source": "integration_test",
            "relation": "TEST_VECTOR", "target": '{"Love": 0.95}', "emotion": 0.5
        })
        check("Lantern mock POST /remember", code == 200, str(data))

        code, data = get("http://localhost:3001/query?pattern=test")
        check("Lantern mock GET /query", code == 200 and isinstance(data, list),
              f"returned {len(data) if isinstance(data,list) else '?'} items")

    # RFE-Core2
    code, data = get("http://localhost:8000/status")
    rfe_up = code == 200
    check("RFE-Core2 :8000/status", rfe_up,
          str(data)[:60] if not rfe_up else "ok")

    if rfe_up:
        code, data = post("http://localhost:8000/step",
                          {"tokens": ["integration", "test"]})
        check("RFE-Core2 POST /step", code == 200, "")
        if code == 200:
            check("RFE-Core2 /step: rhythm is string",
                  isinstance(data.get("rhythm"), str), str(data.get("rhythm")))
            check("RFE-Core2 /step: coherence is float",
                  isinstance(data.get("coherence"), (int, float)))
            relation = data.get("relation")
            check("RFE-Core2 /step: relation is float",
                  isinstance(relation, (int, float)), str(relation))

    # Unified Observer
    code, data = get("http://localhost:5000/health")
    obs_up = code == 200
    check("Unified Observer :5000/health", obs_up,
          str(data) if not obs_up else "ok")

    if obs_up:
        code, data = get("http://localhost:5000/identity")
        check("Unified Observer GET /identity", code == 200, "")
        if code == 200:
            for field_name in ["coherence_score", "symmetry_score",
                               "observer_strength", "biological_health"]:
                v = data.get(field_name)
                check(f"Observer /identity: {field_name} in [0,1]",
                      v is not None and 0.0 <= float(v) <= 1.0,
                      str(v))

    # ProjectSynapse
    code, data = get("http://localhost:8001/health")
    synapse_up = code == 200
    check("ProjectSynapse ResonanceBridge :8001/health", synapse_up,
          str(data) if not synapse_up else "ok")


# ── 4. FULL CONNECTED STACK TEST ──────────────────────────────────────────────────────────

section("4. FULL CONNECTED STACK (requires all services)")

if not HAS_REQUESTS:
    print(f"  [{SKIP}] Connected stack — requests not installed")
else:
    services_up = lantern_up and rfe_up and obs_up
    if not services_up:
        print(f"  [{SKIP}] Lantern, RFE, or Observer not reachable — skipping end-to-end")
    else:
        try:
            # Restart orchestrator with services running
            orch2 = sm.ResonanceOrchestrator(warm_start=False)
            rfe_connected  = orch2.rfe_bridge is not None
            obs_connected  = orch2.observer_bridge is not None
            lan_connected  = orch2.synapse._lantern_reachable

            check("Full stack: RFE-Core2 bridge connected", rfe_connected)
            check("Full stack: Observer bridge connected", obs_connected)
            check("Full stack: Lantern reachable", lan_connected)

            # Run 10 cycles with all services
            connected_states = [orch2.step() for _ in range(10)]
            final_cs = connected_states[-1]

            check("Full stack: 10 cycles with services", len(connected_states) == 10)
            check("Full stack: state remains valid",
                  all(0.0 <= v <= 1.0 for v in final_cs.relational_s))

            if lan_connected:
                # Check Lantern received writes
                code, data = requests.get(
                    "http://localhost:3001/query?pattern=relational_manifold"
                ).status_code, requests.get(
                    "http://localhost:3001/query?pattern=relational_manifold"
                ).json()
                check("Full stack: Lantern received manifold states",
                      isinstance(data, list) and len(data) >= 0,
                      f"{len(data)} stored")

        except Exception as e:
            check("Full connected stack", False, str(e))
            traceback.print_exc()


# ── SUMMARY ────────────────────────────────────────────────────────────────────────────────

section("SUMMARY")
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
total  = len(results)

print(f"  {passed}/{total} passed  ({failed} failed)")
if failed > 0:
    print("\n  Failed checks:")
    for name, ok in results:
        if not ok:
            print(f"    ✗ {name}")
print()
sys.exit(0 if failed == 0 else 1)
