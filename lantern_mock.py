"""
lantern_mock.py — Python mock for the Lantern HTTP daemon.

Implements the same API as the Rust/Tauri Lantern daemon on :3001:
  GET  /health          → {"status": "ok"}
  POST /remember        → stores a memory node
  GET  /query?pattern=X → returns matching stored targets

This runs in-process during development/testing when the Rust daemon
is not available. Data is in-memory only (resets on restart).

Usage: python lantern_mock.py
"""
from __future__ import annotations

import json
import threading
from typing import Any, Dict, List
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Lantern Mock", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

_lock: threading.Lock = threading.Lock()
_nodes: List[Dict[str, Any]] = []


@app.get("/health")
def health():
    with _lock:
        return {"status": "ok", "nodes": len(_nodes)}


@app.post("/remember")
def remember(payload: Dict[str, Any]):
    """Store a memory node. Payload matches what sovereign_manifold sends."""
    with _lock:
        _nodes.append(payload)
    return {"ok": True, "total": len(_nodes)}


@app.get("/query")
def query(pattern: str = Query(default=""), limit: int = Query(default=10)):
    """Return target strings for nodes whose source or source_type matches pattern."""
    with _lock:
        matches = [
            n.get("target", "{}")
            for n in _nodes
            if pattern.lower() in str(n.get("source_type", "")).lower()
            or pattern.lower() in str(n.get("source", "")).lower()
        ]
    return matches[-limit:]


if __name__ == "__main__":
    print("[LANTERN-MOCK] Starting on :3001")
    uvicorn.run(app, host="0.0.0.0", port=3001, log_level="warning")
