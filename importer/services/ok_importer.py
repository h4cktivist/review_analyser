import hashlib
import time
import requests
from datetime import datetime

from django.conf import settings
from django.utils.timezone import make_aware

OK_API_URL = "https://api.ok.ru/fb.do"
OK_APPLICATION_PUBLIC_KEY = "CGBPKMNGDIHBABABA"


def _call_api(method: str, params: dict = None) -> dict:
    if params is None:
        params = {}

    base_params = {
        "application_key": OK_APPLICATION_PUBLIC_KEY,
        "method": method,
        "format": "json",
        **params,
    }

    sorted_items = sorted(base_params.items())
    sig_string = "".join(f"{k}={v}" for k, v in sorted_items)
    sig_string += settings.OK_SESSION_SECRET_KEY
    sig = hashlib.md5(sig_string.encode("utf-8")).hexdigest()

    all_params = {
        **base_params,
        "access_token": settings.OK_ACCESS_TOKEN,
        "sig": sig,
    }

    response = requests.post(OK_API_URL, data=all_params, timeout=30)
    response.raise_for_status()
    return response.json()


def _parse_date(raw_date) -> datetime | None:
    try:
        if str(raw_date).isdigit():
            return make_aware(datetime.fromtimestamp(int(raw_date)))
        return make_aware(datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S"))
    except Exception:
        return None


def _get_discussions(group_id: str) -> list:
    result = _call_api("discussions.getList", {"gid": group_id, "count": 100})
    if result and "discussions" in result:
        return result["discussions"]
    return []


def _get_comments(discussion_id: str, discussion_type: str) -> list:
    all_comments = []
    offset = 0

    while True:
        result = _call_api(
            "discussions.getComments",
            {
                "discussionId": discussion_id,
                "discussionType": discussion_type,
                "count": 100,
                "offset": offset,
            },
        )

        if not result or "comments" not in result:
            break

        comments = result["comments"]
        if not comments:
            break

        for comment in comments:
            text = comment.get("text")
            raw_date = comment.get("date")
            comment_id = comment.get("id")

            if not text or not raw_date or not comment_id:
                continue

            if text.startswith("#ud"):
                continue

            date = _parse_date(raw_date)
            if not date:
                continue

            all_comments.append(
                {
                    "comment_id": comment_id,
                    "text": text.strip(),
                    "date": date,
                }
            )

        if len(comments) < 100:
            break

        offset += 100
        time.sleep(0.2)

    return all_comments


def fetch_ok_comments(group_id: str) -> list:
    collected: dict[str, dict] = {}

    discussions = _get_discussions(group_id)

    for discussion in discussions:
        discussion_id = discussion.get("object_id")
        discussion_type = discussion.get("object_type", "GROUP_TOPIC")

        if not discussion_id:
            continue

        comments = _get_comments(discussion_id, discussion_type)

        for comment in comments:
            key = comment["comment_id"]
            if key not in collected:
                collected[key] = {
                    "text": comment["text"],
                    "date": comment["date"],
                }

    time.sleep(0.5)

    return list(collected.values())
