import os
from datetime import datetime, timezone
from typing import Optional

import requests


class MainAppClient:
    def __init__(self):
        base_url = os.getenv("MAIN_APP_API_URL", "http://127.0.0.1:8000/api").rstrip("/")
        worker_token = os.getenv("EVENTS_WORKER_TOKEN", "")
        if not worker_token:
            raise RuntimeError("EVENTS_WORKER_TOKEN must be set for worker service")

        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Token {worker_token}",
                "Content-Type": "application/json",
            }
        )

    def get_latest_event_date(self) -> Optional[datetime]:
        response = self.session.get(f"{self.base_url}/events/latest-date/", timeout=20)
        response.raise_for_status()
        payload = response.json()
        latest_date = payload.get("last_event_date")
        if not latest_date:
            return None

        parsed = datetime.fromisoformat(latest_date.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    def send_event(self, event_name: str, meeting_date: str, is_rent: bool = False):
        if " " in meeting_date:
            event_dt = datetime.strptime(meeting_date, "%Y-%m-%d %H:%M")
        else:
            event_dt = datetime.strptime(meeting_date, "%Y-%m-%d")
        event_dt = event_dt.replace(tzinfo=timezone.utc)

        payload = {
            "name": event_name,
            "date": event_dt.isoformat().replace("+00:00", "Z"),
            "is_rent": is_rent,
        }
        response = self.session.post(f"{self.base_url}/events/", json=payload, timeout=20)
        if response.status_code not in (200, 201):
            raise RuntimeError(f"Failed to create event: {response.status_code} {response.text}")
