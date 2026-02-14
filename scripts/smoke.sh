#!/bin/bash
set -e

# Smoke test for Heidi CLI
# Tests basic functionality: paths, start backend, start ui, health check, stop

echo "=== Heidi CLI Smoke Test ==="
echo ""

# Test 1: heidi paths
echo "[1/5] Testing heidi paths..."
heidi paths
echo "✓ heidi paths works"
echo ""

# Test 2: Start backend
echo "[2/5] Starting backend..."
heidi start backend &
BACKEND_PID=$!
sleep 5

# Test 3: Start UI (no open)
echo "[3/5] Starting UI..."
heidi start ui --no-ui-update --no-open &
UI_PID=$!
sleep 8

# Test 4: Health check
echo "[4/5] Checking backend health..."
if curl -s http://localhost:7777/health > /dev/null 2>&1; then
    echo "✓ Backend health check passed"
else
    echo "✗ Backend health check failed"
    kill $BACKEND_PID $UI_PID 2>/dev/null || true
    exit 1
fi

# Test 5: Stop services
echo "[5/5] Stopping services..."
heidi start stop
echo "✓ Services stopped"

echo ""
echo "=== Smoke Test Passed ==="
exit 0
