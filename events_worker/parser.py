import re
from datetime import datetime, timedelta
from typing import Optional

import requests
from bs4 import BeautifulSoup


class TKTOEventParser:
    BASE_URL = "https://kto72.ru"
    EVENTS_URL = f"{BASE_URL}/api/events.php"

    def __init__(self, start_date: datetime, days_ahead: int = 30):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        self.start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        self.end_date = self.start_date + timedelta(days=days_ahead)

    def get_page(self, page: int = 1) -> Optional[str]:
        try:
            response = self.session.get(self.EVENTS_URL, params={"page": page}, timeout=15)
            response.encoding = "utf-8"
            return response.text
        except Exception:
            return None

    def parse_date_string(self, date_str: str):
        if not date_str:
            return None
        parts = [part.strip() for part in date_str.strip().split(",")]
        if not parts:
            return None

        result = {"date": None, "times": []}
        date_part = parts[0].lower()
        for part in parts[1:]:
            result["times"].extend(re.findall(r"(\d{1,2}:\d{2})", part))

        today = datetime.now()
        if "сегодня" in date_part:
            result["date"] = today.strftime("%Y-%m-%d")
        elif "завтра" in date_part:
            result["date"] = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            date_match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", date_part)
            if date_match:
                day, month, year = date_match.groups()
                try:
                    result["date"] = datetime(int(year), int(month), int(day)).strftime("%Y-%m-%d")
                except ValueError:
                    return None

        return result if result["date"] else None

    def is_date_valid(self, event_date_str: str) -> bool:
        try:
            event_date = datetime.strptime(event_date_str[:10], "%Y-%m-%d")
            return self.start_date <= event_date <= self.end_date
        except Exception:
            return False

    def parse_is_rent(self, card) -> bool:
        """Метка аренды: span.events__item-branch с title или текстом «Аренда»."""
        for span in card.find_all("span", class_="events__item-branch"):
            title = (span.get("title") or "").strip()
            text = span.get_text(strip=True)
            if title == "Аренда" or text == "Аренда":
                return True
        return False

    def parse_events_from_html(self, html: str):
        soup = BeautifulSoup(html, "html.parser")
        events = []
        cards = soup.find_all("div", class_="js-events__item")
        if not cards:
            cards = soup.find_all("div", class_="events__item")

        for card in cards:
            try:
                title_elem = card.find("a")
                if not title_elem:
                    continue
                title = title_elem.get_text().strip()
                if not title or len(title) < 3 or title.lower() == "купить билет":
                    continue

                time_elem = card.find("div", class_="events__item-time")
                if not time_elem:
                    time_elem = card.find("div", string=re.compile(r"Сегодня|Завтра|\d{1,2}\.\d{1,2}\.\d{4}"))
                if not time_elem:
                    continue

                date_info = self.parse_date_string(time_elem.get_text().strip())
                if not date_info:
                    continue

                is_rent = self.parse_is_rent(card)
                if date_info["times"]:
                    for item_time in date_info["times"]:
                        event = {
                            "event_name": title,
                            "meeting_date": f"{date_info['date']} {item_time}",
                            "is_rent": is_rent,
                        }
                        if self.is_date_valid(event["meeting_date"]):
                            events.append(event)
                else:
                    event = {"event_name": title, "meeting_date": date_info["date"], "is_rent": is_rent}
                    if self.is_date_valid(event["meeting_date"]):
                        events.append(event)
            except Exception:
                continue
        return events

    def parse_all(self, max_pages: int = 50):
        all_events = []
        page = 1
        pages_without_new = 0
        has_more = True

        while has_more and page <= max_pages and pages_without_new < 3:
            html = self.get_page(page)
            if not html:
                break
            events = self.parse_events_from_html(html)

            if events:
                valid_events = [event for event in events if self.is_date_valid(event["meeting_date"])]
                if valid_events:
                    all_events.extend(valid_events)
                    pages_without_new = 0
                else:
                    pages_without_new += 1

                parsed_dates = []
                for event in events:
                    try:
                        parsed_dates.append(datetime.strptime(event["meeting_date"][:10], "%Y-%m-%d"))
                    except ValueError:
                        continue
                if parsed_dates and min(parsed_dates) < self.start_date:
                    break
            else:
                pages_without_new += 1

            if len(events) < 10:
                has_more = False
            page += 1

        seen = set()
        unique_events = []
        for event in all_events:
            key = (event["event_name"], event["meeting_date"])
            if key not in seen:
                seen.add(key)
                unique_events.append(event)

        unique_events.sort(key=lambda item: item["meeting_date"])
        return unique_events
