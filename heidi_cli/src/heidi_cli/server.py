from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn


app = FastAPI(title="Heidi CLI Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    prompt: str
    executor: str = "copilot"
    workdir: Optional[str] = None


class LoopRequest(BaseModel):
    task: str
    executor: str = "copilot"
    max_retries: int = 2
    workdir: Optional[str] = None


class RunResponse(BaseModel):
    run_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None


_bg_tasks: dict[str, asyncio.Task] = {}


def _read_text_if_exists(path: Path) -> Optional[str]:
    try:
        if path.exists():
            return path.read_text(errors="replace")
    except Exception:
        return None
    return None


async def _execute_run(run_id: str, request: RunRequest) -> None:
    from .logging import HeidiLogger
    from .orchestrator.loop import pick_executor

    HeidiLogger.init_run(run_id)

    workdir = Path(request.workdir) if request.workdir else Path.cwd()
    run_dir = HeidiLogger.get_run_dir()

    try:
        executor = pick_executor(request.executor)
        result = await executor.run(request.prompt, workdir)
        if run_dir:
            (run_dir / "result.txt").write_text(result.output)
        HeidiLogger.write_run_meta({"status": "completed", "ok": result.ok})
        if not result.ok:
            HeidiLogger.write_run_meta({"error": result.output})
    except Exception as e:
        if run_dir:
            (run_dir / "error.txt").write_text(str(e))
        HeidiLogger.write_run_meta({"status": "failed", "error": str(e)})
    finally:
        _bg_tasks.pop(run_id, None)


async def _execute_loop(run_id: str, request: LoopRequest) -> None:
    from .logging import HeidiLogger
    from .orchestrator.loop import run_loop

    HeidiLogger.init_run(run_id)

    workdir = Path(request.workdir) if request.workdir else Path.cwd()
    run_dir = HeidiLogger.get_run_dir()

    try:
        result = await run_loop(
            task=request.task,
            executor=request.executor,
            max_retries=request.max_retries,
            workdir=workdir,
        )
        if run_dir:
            (run_dir / "result.txt").write_text(result)
        HeidiLogger.write_run_meta({"status": "completed", "result": result})
    except Exception as e:
        if run_dir:
            (run_dir / "error.txt").write_text(str(e))
        HeidiLogger.write_run_meta({"status": "failed", "error": str(e)})
    finally:
        _bg_tasks.pop(run_id, None)


@app.get("/")
async def root():
    return {"status": "ok", "service": "heidi-cli"}


@app.get("/runs")
async def list_runs(limit: int = 10):
    from .config import ConfigManager

    runs_dir = ConfigManager.RUNS_DIR
    if not runs_dir.exists():
        return []

    runs = []
    for run_path in sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        run_json = run_path / "run.json"
        if run_json.exists():
            meta = json.loads(run_json.read_text())
            runs.append({
                "run_id": run_path.name,
                "status": meta.get("status", "unknown"),
                "task": meta.get("task", meta.get("prompt", "")),
                "executor": meta.get("executor", ""),
            })

    return runs


@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    from .config import ConfigManager

    run_dir = ConfigManager.RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    run_json = run_dir / "run.json"
    transcript = run_dir / "transcript.jsonl"

    result = {"run_id": run_id}

    if run_json.exists():
        result["meta"] = json.loads(run_json.read_text())

    result_text = _read_text_if_exists(run_dir / "result.txt")
    error_text = _read_text_if_exists(run_dir / "error.txt")
    if result_text is not None:
        result["result"] = result_text
    if error_text is not None:
        result["error"] = error_text

    if transcript.exists():
        events = []
        for line in transcript.read_text().strip().split("\n"):
            if line:
                events.append(json.loads(line))
        result["events"] = events

    return result


@app.get("/runs/{run_id}/stream")
async def stream_run(run_id: str):
    from .config import ConfigManager

    run_dir = ConfigManager.RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_generator():
        transcript = run_dir / "transcript.jsonl"
        if not transcript.exists():
            return

        last_pos = 0
        while True:
            await asyncio.sleep(1)
            content = transcript.read_text()
            if len(content) > last_pos:
                new_content = content[last_pos:]
                last_pos = len(content)
                for line in new_content.strip().split("\n"):
                    if line:
                        yield f"data: {line}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/run", response_model=RunResponse)
async def run(request: RunRequest):
    from .logging import HeidiLogger

    workdir = Path(request.workdir) if request.workdir else None
    if not workdir:
        workdir = Path.cwd()

    run_id = HeidiLogger.init_run()
    HeidiLogger.write_run_meta({
        "run_id": run_id,
        "prompt": request.prompt,
        "executor": request.executor,
        "workdir": str(workdir),
        "status": "running",
    })

    task = asyncio.create_task(_execute_run(run_id, request))
    _bg_tasks[run_id] = task
    return RunResponse(run_id=run_id, status="running")


@app.post("/loop", response_model=RunResponse)
async def loop(request: LoopRequest):
    from .logging import HeidiLogger

    workdir = Path(request.workdir) if request.workdir else None
    if not workdir:
        workdir = Path.cwd()

    run_id = HeidiLogger.init_run()
    HeidiLogger.write_run_meta({
        "run_id": run_id,
        "task": request.task,
        "executor": request.executor,
        "max_retries": request.max_retries,
        "workdir": str(workdir),
        "status": "running",
    })

    task = asyncio.create_task(_execute_loop(run_id, request))
    _bg_tasks[run_id] = task
    return RunResponse(run_id=run_id, status="running")


@app.get("/agents")
async def list_agents():
    from .orchestrator.registry import AgentRegistry

    agents = AgentRegistry.list_agents()
    return [{"name": n, "description": d} for n, d in agents]


def start_server(host: str = "0.0.0.0", port: int = 7777):
    uvicorn.run(app, host=host, port=port)
