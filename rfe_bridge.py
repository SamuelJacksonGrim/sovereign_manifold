"""rfe_bridge.py — RFE-Core2 ↔ Sovereign Manifold integration bridge.

Maps rfe-core2 StepResponse fields to 15-node relational perturbation vectors.
Imported by sovereign_manifold.py when rfe-core2 is running on :8000.
"""
import numpy as np
from typing import Optional, List

try:
    import requests as _requests
    _REQ = True
except ImportError:
    _REQ = False

# StepResponse field → [(node_index, scale), ...]
# Positive scale: field value above 0.5 pushes node up.
# Negative scale: field value above 0.5 pushes node down.
_FIELD_MAP: dict = {
    "coherence":        [(10,  0.030), (8,  0.020)],  # Transparency, Integrity
    "rhythm":           [(9,   0.030)],                 # Resilience
    "prediction_error": [(7,  -0.025), (4, -0.015)],  # Autonomy↓, Self↓
    "field_energy":     [(0,   0.020), (4,  0.020)],  # Love, Self
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

        Returns None if rfe-core2 is unreachable or response malformed.
        Values are centered at 0.5: above 0.5 pushes mapped nodes up,
        below 0.5 pushes them down. Capped at ±_MAX_DELTA per node.
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
        for field, mappings in _FIELD_MAP.items():
            val = data.get(field)
            if val is None:
                continue
            deviation = float(val) - 0.5
            for node_idx, scale in mappings:
                if node_idx < n_nodes:
                    delta[node_idx] += deviation * scale * 2.0

        return np.clip(delta, -_MAX_DELTA, _MAX_DELTA)
