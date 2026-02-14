#!/bin/bash
# Smoke test for OpenCode OpenAI connection
# Run: ./scripts/smoke_opencode_openai.sh

set -e

echo "=========================================="
echo "OpenCode OpenAI Smoke Test"
echo "=========================================="

BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:7777}"
FAILED=0

echo ""
echo "=== Test 1: Check heidi version ==="
heidi --version
echo "✓ heidi installed"

echo ""
echo "=== Test 2: Check OpenCode version ==="
opencode --version
echo "✓ OpenCode installed"

echo ""
echo "=== Test 3: heidi connect opencode openai --verify --json ==="
OUTPUT=$(heidi connect opencode openai --verify --json 2>&1) || true
echo "$OUTPUT"
if echo "$OUTPUT" | grep -q '"ok":true'; then
    echo "✓ Verify shows connected"
else
    echo "⚠ Not connected (expected if not OAuth'd yet)"
fi

echo ""
echo "=== Test 4: Backend /api/connect/opencode/openai/status ==="
STATUS=$(curl -s "$BACKEND_URL/api/connect/opencode/openai/status" 2>/dev/null) || echo "{}"
echo "$STATUS"
if echo "$STATUS" | grep -q '"connected":true'; then
    echo "✓ Backend status shows connected"
else
    echo "⚠ Not connected"
fi

echo ""
echo "=== Test 5: Backend test endpoint ==="
TEST=$(curl -s -X POST "$BACKEND_URL/api/connect/opencode/openai/test" 2>/dev/null) || echo '{"pass":false}'
echo "$TEST"
if echo "$TEST" | grep -q '"pass":true'; then
    echo "✓ Test endpoint works"
else
    echo "⚠ Test endpoint (may need OAuth)"
fi

echo ""
echo "=== Test 6: opencode models openai ==="
MODELS=$(opencode models openai 2>&1) || echo ""
if [ -n "$MODELS" ]; then
    echo "✓ opencode models openai returns models"
    echo "$MODELS"
else
    echo "⚠ No models (needs OAuth)"
fi

echo ""
echo "=========================================="
echo "Smoke test complete"
echo "=========================================="
