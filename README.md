# Heidi CLI

Heidi is a Python CLI that orchestrates agent-style workflows across multiple executors (Copilot SDK, Jules, OpenCode) and can also run as a small HTTP server for OpenWebUI integration.

## Install

```bash
python -m pip install -e "./.[dev]"
```

## Initialize + auth

```bash
heidi init
heidi auth gh
heidi auth status
```

## Copilot

```bash
heidi copilot status
heidi copilot chat "hello" --timeout 120
heidi copilot doctor
```

## Loop

```bash
heidi loop "create hello.py prints hello" --executor copilot
heidi runs
```

## Server (OpenWebUI)

```bash
heidi serve --port 7777
```

