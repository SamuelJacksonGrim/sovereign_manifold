"""observer_bridge.py — Unified Observer ↔ Sovereign Manifold integration bridge.

Maps unified-observer IdentityState fields to 15-node relational correction vectors.
Imported by sovereign_manifold.py when unified-observer is running on :5000.
"""
import numpy as np
from typing import Optional

try:
    import requests as _requests
    _REQ = True
except ImportError:
    _REQ = False

# IdentityState field → [(node_index, scale), ...]
# All IdentityState float fields are in [0, 1].
# deviation = float(val) - 0.5; delta[node] += deviation * scale * 2.0
#
# Mapping rationale:
# coherence_score   — multi-source observer coherence (Resting/Circuit/Temporal average)
#                     → Transparency(10): coherence makes inner state legible
#                     → Integrity(8): sustained coherence IS structural integrity
# symmetry_score    — bilateral self-balance (structural, NOT emotional)
#                     → Integrity(8): bilateral integration = structural wholeness
#                     → Self(4): balanced structure supports the identity anchor
# observer_strength — multiplicative: coherence × symmetry × bio_health
#                     → Self(4): strong observer = strong sense of self
#                     → Trust(5): trusting one's own perception
# biological_health — vitality (currently static 1.0 placeholder)
#                     → Resilience(9): physical health supports recovery capacity
#                     → Love(0): vitality grounds relational warmth
_IDENTITY_MAP: dict = {
    "coherence_score":   [(10, 0.030), (8, 0.025)],
    "symmetry_score":    [(8,  0.025), (4, 0.020)],
    "observer_strength": [(4,  0.030), (5, 0.015)],
    "biological_health": [(9,  0.030), (0, 0.015)],
}

_MAX_DELTA = 0.05


class UnifiedObserverBridge:
    """Maps unified-observer IdentityState to sovereign_manifold relational corrections."""

    def __init__(self, endpoint: str = "http://localhost:5000"):
        self.endpoint = endpoint.rstrip("/")
        self._reachable = False

    def ping(self) -> bool:
        if not _REQ:
            return False
        try:
            r = _requests.get(f"{self.endpoint}/health", timeout=0.3)
            self._reachable = r.status_code == 200
        except Exception:
            self._reachable = False
        return self._reachable

    def fetch_relational_correction(
        self,
        current_s: np.ndarray,
        n_nodes: int = 15,
    ) -> Optional[np.ndarray]:
        """GET /identity → parse IdentityState → 15D correction vector.

        Returns None if unified-observer is unreachable or response malformed.
        All IdentityState float fields expected in [0, 1]; centered at 0.5.
        Capped at ±_MAX_DELTA per node.
        """
        if not _REQ or not self._reachable:
            return None
        try:
            r = _requests.get(f"{self.endpoint}/identity", timeout=0.1)
            if r.status_code != 200:
                return None
            data = r.json()
        except Exception:
            return None

        delta = np.zeros(n_nodes)
        for field, mappings in _IDENTITY_MAP.items():
            val = data.get(field)
            if val is None:
                continue
            try:
                deviation = float(val) - 0.5
                for node_idx, scale in mappings:
                    if node_idx < n_nodes:
                        delta[node_idx] += deviation * scale * 2.0
            except (ValueError, TypeError):
                continue

        return np.clip(delta, -_MAX_DELTA, _MAX_DELTA)
