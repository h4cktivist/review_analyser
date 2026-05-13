import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from events_worker.client import MainAppClient
from events_worker.parser import TKTOEventParser

logger = logging.getLogger("events-worker")


@dataclass
class WorkerState:
    last_run_status: str = "never"
    last_run_at: str | None = None
    last_run_added: int = 0
    last_error: str | None = None


def parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


async def run_import(state: WorkerState, run_lock: asyncio.Lock, trigger: str):
    async with run_lock:
        state.last_error = None
        try:
            logger.info("Запуск импорта (%s)", trigger)
            client = MainAppClient()
            latest_event_date = await asyncio.to_thread(client.get_latest_event_date)
            start_date = latest_event_date or datetime.now(timezone.utc)

            days_ahead = int(os.getenv("WORKER_DAYS_AHEAD", "30"))
            parser = TKTOEventParser(start_date=start_date.replace(tzinfo=None), days_ahead=days_ahead)
            events = await asyncio.to_thread(parser.parse_all, 50)

            imported_count = 0
            for event in events:
                try:
                    await asyncio.to_thread(
                        client.send_event,
                        event["event_name"],
                        event["meeting_date"],
                        event.get("is_rent", False),
                    )
                    imported_count += 1
                except Exception as exc:
                    logger.warning("Ошибка отправки события '%s': %s", event["event_name"], exc)

            state.last_run_status = "success"
            state.last_run_at = datetime.now(timezone.utc).isoformat()
            state.last_run_added = imported_count
            logger.info("Импорт завершен (%s): добавлено %s", trigger, imported_count)
            return {"status": "ok", "trigger": trigger, "imported": imported_count, "parsed": len(events)}
        except Exception as exc:
            state.last_run_status = "failed"
            state.last_run_at = datetime.now(timezone.utc).isoformat()
            state.last_error = str(exc)
            logger.exception("Импорт завершился с ошибкой (%s)", trigger)
            raise


async def scheduler_loop(state: WorkerState, run_lock: asyncio.Lock):
    schedule_time = os.getenv("WORKER_SCHEDULE_TIME", "08:00")
    enabled = parse_bool(os.getenv("WORKER_SCHEDULE_ENABLED", "true"), True)
    if not enabled:
        logger.info("Планировщик отключен (WORKER_SCHEDULE_ENABLED=false)")
        return

    hour, minute = [int(part) for part in schedule_time.split(":")]
    last_run_date = None
    logger.info("Планировщик активен, ежедневный запуск в %s UTC", schedule_time)

    while True:
        now = datetime.now(timezone.utc)
        if now.hour == hour and now.minute == minute and last_run_date != now.date():
            try:
                await run_import(state=state, run_lock=run_lock, trigger="schedule")
            except Exception:
                pass
            last_run_date = now.date()
        await asyncio.sleep(20)
