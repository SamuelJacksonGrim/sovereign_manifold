"""
run_observer.py — Start unified-observer on :5000.

Usage: python run_observer.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'unified-observer-architecture'))

# Patch the malformed requirements.txt (has markdown fences) — harmless here
import uvicorn

# Import the server app (starts background thread automatically on import)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'unified-observer-architecture'))
os.chdir(os.path.join(os.path.dirname(__file__), 'unified-observer-architecture'))

from scripts.server import app

if __name__ == "__main__":
    print("[OBS] Starting unified-observer on :5000")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="warning")
