"""
run_rfe.py — Start rfe-core2 REST API on :8000.

Usage: python run_rfe.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rfe-core2'))

from agents.generator import Generator
from loop.autonomous_cycle import AutonomousCycle
from api.inference_api import create_app
import uvicorn

generator = Generator(
    vocab_size=8192, dim=128, depth=4, heads=4,
    ff_mult=4, dropout=0.1,
    auto_decay_interval=500, decay_interval=10,
)
cycle = AutonomousCycle(
    generator=generator, dim=128, use_chorus=True,
    maintenance_interval=200, log_interval=50,
)

app = create_app(cycle, generator)

if __name__ == "__main__":
    print("[RFE] Starting rfe-core2 on :8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
