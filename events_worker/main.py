import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from events_worker.config import load_worker_env
from events_worker.services import WorkerState, parse_bool, run_import, scheduler_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
load_worker_env()

state = WorkerState()
run_lock = asyncio.Lock()
background_scheduler_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global background_scheduler_task

    autostart = parse_bool(os.getenv("WORKER_AUTOSTART", "true"), True)
    if autostart:
        try:
            await run_import(state=state, run_lock=run_lock, trigger="startup")
        except Exception:
            pass

    background_scheduler_task = asyncio.create_task(scheduler_loop(state=state, run_lock=run_lock))
    yield
    if background_scheduler_task:
        background_scheduler_task.cancel()


app = FastAPI(
    title="Events Extractor Worker",
    description="Imports events from KTO and sends them to main API.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "last_run_status": state.last_run_status,
        "last_run_at": state.last_run_at,
        "last_run_added": state.last_run_added,
        "last_error": state.last_error,
    }


@app.post("/run")
async def run_now():
    if run_lock.locked():
        raise HTTPException(status_code=409, detail="Import is already running")
    try:
        return await run_import(state=state, run_lock=run_lock, trigger="manual")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
