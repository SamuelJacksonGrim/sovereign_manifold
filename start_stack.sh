#!/bin/bash
# start_stack.sh — Start the full cognitive stack in the correct order.
#
# Usage: ./start_stack.sh [--test]
#   --test   run test_integration.py after startup
#
# Requires: Python 3.11+, Java 21+, compiled ProjectSynapse_v2.java
# All processes run in the background; logs go to logs/<service>.log

set -e
STACK_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$STACK_DIR/logs"
mkdir -p "$LOG_DIR"

RUN_TESTS=false
[[ "$1" == "--test" ]] && RUN_TESTS=true

cleanup() {
    echo ""
    echo "[STACK] Shutting down..."
    kill $(jobs -p) 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "╔═════════════════════════════════════════════╗"
echo "║        COGNITIVE STACK — STARTUP             ║"
echo "╚═════════════════════════════════════════════╝"
echo ""

# 1. Lantern (memory backbone, no deps)
echo "[1/5] Starting Lantern mock on :3001..."
python3 "$STACK_DIR/lantern_mock.py" > "$LOG_DIR/lantern.log" 2>&1 &
LANTERN_PID=$!

# 2. RFE-Core2 (no deps)
echo "[2/5] Starting RFE-Core2 on :8000..."
python3 "$STACK_DIR/run_rfe.py" > "$LOG_DIR/rfe.log" 2>&1 &
RFE_PID=$!

# 3. Unified Observer (no deps)
echo "[3/5] Starting Unified Observer on :5000..."
python3 "$STACK_DIR/run_observer.py" > "$LOG_DIR/observer.log" 2>&1 &
OBS_PID=$!

# 4. ProjectSynapse (after lantern)
echo "[4/5] Starting ProjectSynapse on :5001/:8001..."
cd "$STACK_DIR/projectsynapse"
java ProjectSynapse_v2 > "$LOG_DIR/synapse.log" 2>&1 &
SYNAPSE_PID=$!
cd "$STACK_DIR"

# Wait for services to be ready
echo ""
echo "Waiting for services..."
sleep 4

# Health checks
ALL_OK=true
for SVC_URL in \
    "Lantern:http://localhost:3001/health" \
    "RFE-Core2:http://localhost:8000/status" \
    "Observer:http://localhost:5000/health" \
    "Synapse:http://localhost:8001/health"; do

    NAME="${SVC_URL%%:*}"
    URL="${SVC_URL#*:}"
    CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$URL" 2>/dev/null || echo "000")
    if [[ "$CODE" == "200" ]]; then
        echo "  ✓ $NAME"
    else
        echo "  ✗ $NAME (HTTP $CODE) — check logs/$( echo $NAME | tr '[:upper:]' '[:lower:]').log"
        ALL_OK=false
    fi
done

echo ""
if $ALL_OK; then
    echo "All services up. Stack is ready."
else
    echo "Some services failed to start. Check logs/ directory."
fi

if $RUN_TESTS; then
    echo ""
    echo "Running integration tests..."
    python3 "$STACK_DIR/test_integration.py"
fi

echo ""
echo "Logs: $LOG_DIR/"
echo "Press Ctrl+C to stop all services."
echo ""

# Keep script alive (services are background jobs)
wait
