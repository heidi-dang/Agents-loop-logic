#!/bin/bash
# Examples for Unified Learning Suite API (Pending integration)

echo "--- GET Models ---"
curl -s http://localhost:8000/v1/models

echo "
--- POST Chat Completions (Success) ---"
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @success_chat.json

echo "
--- POST Chat Completions (Failure - Bad Model) ---"
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @failure_bad_model.json
