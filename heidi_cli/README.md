# Heidi CLI (skeleton)

This is a minimal starter that:
- Chats with GitHub Copilot via the **Copilot Python SDK** (Copilot CLI in server mode).
- Wraps **Jules** and **OpenCode** CLIs (optional).
- Runs a simple "Plan -> Execute batches" loop using a registry of agent prompts.

## Install (editable)

```bash
cd heidi_cli
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick tests

```bash
heidi copilot status
heidi copilot chat "hello"
heidi loop "fix failing tests" --executor copilot
```
