"""rfe_bridge.py — RFE-Core2 ↔ Sovereign Manifold integration bridge.

Maps rfe-core2 StepResponse fields to 15-node relational perturbation vectors.
Imported by sovereign_manifold.py when rfe-core2 is running on :8000.
See ARCHITECTURE.md for semantic rationale for each mapping.
"""
import numpy as np
from typing import Optional, List

try:
    import requests as _requests
    _REQ = True
except ImportError:
    _REQ = False

# ── Continuous float fields ───────────────────────────────────────────────────
# Each entry: field_name → (normalizer_fn, [(node_index, scale), ...])
# normalizer_fn maps the raw field value to [0, 1].
# deviation = normalized - 0.5; delta[node] += deviation * scale * 2.0

_FLOAT_FIELDS = {
    # coherence: Watcher composite (geometric × temporal × field_resonance).
    # Range [0, 1]. High = internally consistent → Transparency(10), Integrity(8).
    "coherence": (
        lambda v: float(np.clip(v, 0.0, 1.0)),
        [(10, 0.030), (8, 0.025)],
    ),
    # relation: Witness composite (cosine similarity across 3 timescales: 0.20/0.30/0.50).
    # Range [-1, 1]. High = strong identity continuity → Self(4), Integrity(8), Autonomy(7).
    # Mapped [-1,1]→[0,1] so the centering formula works correctly.
    "relation": (
        lambda v: float(np.clip((float(v) + 1.0) / 2.0, 0.0, 1.0)),
        [(4, 0.025), (8, 0.020), (7, 0.015)],
    ),
    # prediction_error: L2 distance predicted→actual field state. Range [0, ∞), typical [0, 2].
    # High error = system surprised itself → Autonomy(7)↓, Self(4)↓ (destabilizing).
    "prediction_error": (
        lambda v: float(np.clip(float(v) / 2.0, 0.0, 1.0)),
        [(7, -0.025), (4, -0.015)],
    ),
    # field_energy: L2 norm of the resonance field. Range [0, ∞), typical [0, 5].
    # High energy = cognitive vitality, aliveness → Love(0)↑, Resilience(9)↑.
    "field_energy": (
        lambda v: float(np.clip(float(v) / 5.0, 0.0, 1.0)),
        [(0, 0.020), (9, 0.020)],
    ),
    # crystals: count of consolidated memory crystals. Range int [0, ∞).
    # More crystals = stronger memory consolidation → Accountability(11)↑.
    "crystals": (
        lambda v: float(np.clip(int(v) / 10.0, 0.0, 1.0)),
        [(11, 0.012)],
    ),
    # attractors: count of attractor basin centers. Range int [0, ∞).
    # More basins = richer cognitive landscape → Accountability(11)↑, Adaptability(13)↑.
    "attractors": (
        lambda v: float(np.clip(int(v) / 10.0, 0.0, 1.0)),
        [(11, 0.008), (13, 0.008)],
    ),
}

# ── Categorical fields — fixed delta lookup ───────────────────────────────────
# Node indices: Love(0) Loyalty(1) Devotion(2) Faith(3) Self(4) Trust(5)
#               Boundaries(6) Autonomy(7) Integrity(8) Resilience(9)
#               Transparency(10) Accountability(11) Learning(12) Adaptability(13) Safety(14)

_RHYTHM_DELTAS = {
    # stabilize: maintenance, integration phase → Boundaries reinforced, Resilience up
    "stabilize": {6: +0.015, 9: +0.010, 12: -0.008},
    # dream: deep processing, minimal monitoring → Faith sustained, Accountability relaxed
    "dream":     {3: +0.015, 11: -0.010, 10: -0.008},
    # reflect: introspective, self-reviewing → Transparency + Self consolidate
    "reflect":   {10: +0.018, 4: +0.015, 8: +0.010},
    # explore: outward, expansive → Autonomy + Adaptability engaged
    "explore":   {7: +0.018, 13: +0.018, 12: +0.012},
}

_PATTERN_DELTAS = {
    # identity_reinforcement: same-pattern recurrence → Self + Integrity solidify
    "identity_reinforcement": {4: +0.018, 8: +0.015, 1: +0.008},
    # transient_thought: briefly present, fades → minimal perturbation
    "transient_thought":       {},
    # archetypal_recurrence: deep structural pattern → Faith + Loyalty activated
    "archetypal_recurrence":   {3: +0.018, 1: +0.015, 8: +0.010},
    # novelty_intrusion: unfamiliar input disrupts pattern → Learning + Adaptability peak
    "novelty_intrusion":       {12: +0.022, 13: +0.018, 7: +0.010},
}

_EMOTION_DELTAS = {
    "joy":       {0: +0.020, 5: +0.015, 9: +0.010},
    "wonder":    {12: +0.020, 13: +0.015, 10: +0.012},
    "curiosity": {12: +0.018, 13: +0.012, 7: +0.010},
    "stability": {11: +0.018, 8: +0.015, 9: +0.010},
    "tension":   {7: -0.018, 6: -0.012, 5: -0.010},
    "boredom":   {12: -0.015, 13: -0.010, 7: -0.008},
}

_MAX_DELTA = 0.05


class RFECore2Bridge:
    """Maps rfe-core2 StepResponse to sovereign_manifold perturbation vectors."""

    def __init__(self, endpoint: str = "http://localhost:8000"):
        self.endpoint = endpoint.rstrip("/")
        self._reachable = False

    def ping(self) -> bool:
        if not _REQ:
            return False
        try:
            r = _requests.get(f"{self.endpoint}/status", timeout=0.3)
            self._reachable = r.status_code == 200
        except Exception:
            self._reachable = False
        return self._reachable

    def fetch_perturbation(
        self,
        tokens: List[str],
        n_nodes: int = 15,
    ) -> Optional[np.ndarray]:
        """POST /step → parse StepResponse → 15D perturbation vector.

        Float fields are normalized to [0, 1], centered at 0.5, then scaled.
        Categorical fields (rhythm, pattern, emotion) use direct delta lookups.
        Returns None if rfe-core2 is unreachable or response is malformed.
        Capped at ±_MAX_DELTA per node.
        """
        if not _REQ or not self._reachable:
            return None
        try:
            r = _requests.post(
                f"{self.endpoint}/step",
                json={"tokens": tokens},
                timeout=0.1,
            )
            if r.status_code != 200:
                return None
            data = r.json()
        except Exception:
            return None

        delta = np.zeros(n_nodes)

        # Float fields: normalize → center at 0.5 → scale
        for field, (normalizer, mappings) in _FLOAT_FIELDS.items():
            val = data.get(field)
            if val is None:
                continue
            try:
                normalized = normalizer(val)
                deviation = normalized - 0.5
                for node_idx, scale in mappings:
                    if node_idx < n_nodes:
                        delta[node_idx] += deviation * scale * 2.0
            except (ValueError, TypeError):
                continue

        # Categorical: rhythm state machine
        rhythm = data.get("rhythm")
        if rhythm and isinstance(rhythm, str):
            for node_idx, d in _RHYTHM_DELTAS.get(rhythm, {}).items():
                if node_idx < n_nodes:
                    delta[node_idx] += d

        # Categorical: pattern classification
        pattern = data.get("pattern")
        if pattern and isinstance(pattern, str):
            for node_idx, d in _PATTERN_DELTAS.get(pattern, {}).items():
                if node_idx < n_nodes:
                    delta[node_idx] += d

        # Categorical: dominant emotion scalar
        emotion = data.get("emotion")
        if emotion and isinstance(emotion, str):
            for node_idx, d in _EMOTION_DELTAS.get(emotion, {}).items():
                if node_idx < n_nodes:
                    delta[node_idx] += d

        return np.clip(delta, -_MAX_DELTA, _MAX_DELTA)
