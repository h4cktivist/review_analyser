from datetime import datetime
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class OtzovikReviewsParser:
    def __init__(self, reviews_url: str, from_date: Optional[datetime] = None):
        self.reviews_url = reviews_url.rstrip("/")
        self.from_date = from_date

    def parse(self) -> List[Dict]:
        page = 1
        results = []

        while True:
            url = f"{self.reviews_url}/?page={page}"
            response = requests.get(url, headers=HEADERS, timeout=15)

            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            reviews = soup.select(".item-right")

            if not reviews:
                break

            for review in reviews:
                parsed = self._parse_review(review)

                if not parsed:
                    continue

                if self.from_date and parsed["date"] <= self.from_date:
                    return results

                results.append(parsed)

            page += 1

        return results

    def _parse_review(self, review) -> Optional[Dict]:
        text_block = review.select_one(".review-teaser")
        date_block = review.select_one(".review-postdate")

        if not text_block or not date_block:
            return None

        text = text_block.get_text(strip=True)

        date_iso = date_block.get("content")
        if not date_iso:
            return None

        try:
            date = datetime.fromisoformat(date_iso)
        except ValueError:
            return None

        return {
            "text": text,
            "date": date
        }

    @staticmethod
    def _parse_date(raw: str) -> Optional[datetime]:
        try:
            return datetime.strptime(raw, "%d.%m.%Y")
        except ValueError:
            return None
