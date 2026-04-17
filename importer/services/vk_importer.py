import aiohttp
import asyncio
from datetime import datetime
import ssl

from django.utils.timezone import make_aware

VK_API_URL = "https://api.vk.com/method"
VK_VERSION = "5.199"
RATE_LIMIT_DELAY = 0.35
FLOOD_CONTROL_ERROR_CODE = 9
FLOOD_RETRY_ATTEMPTS = 5
FLOOD_RETRY_BASE_DELAY = 1.0


class VKAPIError(Exception):
    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


class VKClient:
    def __init__(self, token: str):
        self.token = token
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def call(self, method: str, params: dict):
        request_params = dict(params)
        request_params.update({
            "access_token": self.token,
            "v": VK_VERSION,
        })

        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            for attempt in range(FLOOD_RETRY_ATTEMPTS):
                async with session.get(
                    f"{VK_API_URL}/{method}",
                    params=request_params
                ) as resp:
                    data = await resp.json()

                if "error" not in data:
                    return data["response"]

                error = data["error"]
                error_code = error.get("error_code")
                error_message = error.get("error_msg", "Unknown VK API error")

                if (
                    error_code == FLOOD_CONTROL_ERROR_CODE
                    and attempt < FLOOD_RETRY_ATTEMPTS - 1
                ):
                    await asyncio.sleep(FLOOD_RETRY_BASE_DELAY * (2 ** attempt))
                    continue

                raise VKAPIError(error_message, code=error_code)


class VKReviewsParser:
    def __init__(self, group_id: str, token: str, from_date=None):
        self.group_id = group_id
        self.client = VKClient(token)
        self.from_ts = int(from_date.timestamp()) if from_date else 0
        self._resolved_owner_id = None

    async def _resolve_group_id(self) -> int:
        if self._resolved_owner_id is not None:
            return self._resolved_owner_id

        response = await self.client.call("utils.resolveScreenName", {"screen_name": self.group_id})
        if response["type"] != "group":
            raise ValueError(f"{self.group_id} is not a VK group")
        self._resolved_owner_id = response["object_id"] * -1
        return self._resolved_owner_id

    async def fetch_posts_until_date(self):
        offset = 0
        count = 100
        posts = []

        while True:
            response = await self.client.call("wall.get", {
                "owner_id": self.group_id,
                "count": count,
                "offset": offset,
            })
            await asyncio.sleep(RATE_LIMIT_DELAY)

            items = response.get("items", [])
            if not items:
                break

            for post in items:
                post_date = post.get("date")
                if post_date is None:
                    continue

                if post_date < self.from_ts:
                    return posts

                posts.append(post)

            offset += count

        return posts

    async def fetch_comments(self, post_id: int):
        offset = 0
        count = 100
        comments = []

        while True:
            response = await self.client.call("wall.getComments", {
                "owner_id": await self._resolve_group_id(),
                "post_id": post_id,
                "count": count,
                "offset": offset,
                "preview_length": 0,
                "sort": "desc",
            })
            await asyncio.sleep(RATE_LIMIT_DELAY)

            items = response.get("items", [])
            if not items:
                break

            for comment in items:
                comment_date = comment.get("date")
                if comment_date is None:
                    continue

                if comment_date < self.from_ts:
                    return comments

                if comment.get("text") and len(comment.get("text")) > 0:
                    comment_payload = {
                        "text": comment["text"],
                        "date": make_aware(
                            datetime.fromtimestamp(comment_date)
                        ),
                        "external_id": f'vk_{post_id}_{comment.get("id", "unknown")}',
                    }
                    comments.append(comment_payload)

            offset += count

        return comments

    async def parse(self):
        posts = await self.fetch_posts_until_date()
        result = []

        for post in posts:
            if post.get("comments", {}).get("count", 0) == 0:
                continue

            post_id = post.get("id")
            if post_id is None:
                continue

            post_comments = await self.fetch_comments(post_id)
            result.extend(post_comments)

        return result
