"""
run_sustained.py — Long-running sovereign manifold with telemetry logging.

Runs the ResonanceOrchestrator continuously at ~10Hz.
Every REPORT_EVERY cycles: prints a state snapshot.
Every WITNESS_PUSH_EVERY cycles: saves Witness to disk (GitHub push handled externally).
Logs structured JSON to logs/manifold_telemetry.jsonl for later analysis.

Run: python3 run_sustained.py
Stop: Ctrl+C (Witness saves on exit)
"""
import sys, os, json, time, signal, atexit
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sovereign_manifold'))

import numpy as np
import sovereign_manifold as sm

REPORT_EVERY       = 50    # print to stdout
TELEMETRY_EVERY    = 10    # write to jsonl
TARGET_HZ          = 10.0
LOG_PATH           = os.path.join(os.path.dirname(__file__), 'logs', 'manifold_telemetry.jsonl')

orch = sm.ResonanceOrchestrator(warm_start=True, e8_input_dim=16)
period = 1.0 / TARGET_HZ
t_start = time.time()
wall_start = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
telemetry_file = open(LOG_PATH, 'a', buffering=1)  # line-buffered

def flush_and_save():
    orch.witness.save(force=True)
    telemetry_file.flush()
    elapsed = time.time() - t_start
    print(f"\n[SUSTAINED] Saved. Cycle {orch.cycle} | {elapsed:.1f}s elapsed | "
          f"{orch.cycle / max(elapsed, 1):.1f}Hz actual")

atexit.register(flush_and_save)
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

print(f"\n{'═'*65}")
print(f"  SUSTAINED RUN — started {wall_start}")
print(f"  Target: {TARGET_HZ}Hz  |  Report every {REPORT_EVERY} cycles")
print(f"  Telemetry: {LOG_PATH}")
print(f"{'═'*65}\n")

cycle_times = []

try:
    while True:
        t0 = time.time()
        state = orch.step()
        dt = time.time() - t0
        cycle_times.append(dt)
        if len(cycle_times) > 100:
            cycle_times.pop(0)

        if orch.cycle % TELEMETRY_EVERY == 0:
            try:
                rec = {
                    "cycle":        int(orch.cycle),
                    "wall_time":    round(time.time() - t_start, 2),
                    "dissonance":   round(float(state.dissonance), 6),
                    "lyapunov_V":   round(float(state.lyapunov_V), 6),
                    "mode":         str(state.processing_mode),
                    "valence":      round(float(state.emotion.valence), 4),
                    "arousal":      round(float(state.emotion.arousal), 4),
                    "frustration":  bool(state.frustration),
                    "e8_alpha":     round(float(state.e8_weights.get("alpha", 0)), 4),
                    "e8_beta":      round(float(state.e8_weights.get("beta", 0)), 4),
                    "relational_s": [round(float(v), 4) for v in state.relational_s],
                    "avg_cycle_ms": round(1000 * sum(cycle_times) / len(cycle_times), 2),
                }
                telemetry_file.write(json.dumps(rec) + "\n")
            except Exception as e:
                print(f"[TELEMETRY ERROR] {e}", flush=True)

        if orch.cycle % REPORT_EVERY == 0:
            elapsed = time.time() - t_start
            hz = orch.cycle / max(elapsed, 1)
            low = [(sm.NODE_NAMES[i], round(float(state.relational_s[i]), 3))
                   for i in range(sm.N_NODES) if state.relational_s[i] < 0.88]
            low_str = "  LOW:" + str(low) if low else ""
            print(f"[{orch.cycle:6d}] {state.processing_mode:<9s} "
                  f"d={state.dissonance:.4f} V={state.lyapunov_V:.5f} "
                  f"em(v={state.emotion.valence:.3f} a={state.emotion.arousal:.3f}) "
                  f"{hz:.1f}Hz{low_str}")

        sleep_t = period - (time.time() - t0)
        if sleep_t > 0:
            time.sleep(sleep_t)

except KeyboardInterrupt:
    pass
