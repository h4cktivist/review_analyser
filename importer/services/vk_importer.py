import aiohttp
import asyncio
from datetime import datetime
import ssl

from django.utils.timezone import make_aware

VK_API_URL = "https://api.vk.com/method"
VK_VERSION = "5.199"
RATE_LIMIT_DELAY = 0.35


class VKClient:
    def __init__(self, token: str):
        self.token = token
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def call(self, method: str, params: dict):
        params.update({
            "access_token": self.token,
            "v": VK_VERSION,
        })

        connector = aiohttp.TCPConnector(ssl=self.ssl_context)

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                f"{VK_API_URL}/{method}",
                params=params
            ) as resp:
                data = await resp.json()

                if "error" in data:
                    raise Exception(data["error"]["error_msg"])

                return data["response"]


class VKReviewsParser:
    def __init__(self, group_id: str, token: str, from_date=None):
        self.group_id = group_id
        self.client = VKClient(token)
        self.from_ts = int(from_date.timestamp()) if from_date else 0

    async def _resolve_group_id(self) -> int:
        response = await self.client.call("utils.resolveScreenName", {"screen_name": self.group_id})
        if response["type"] != "group":
            raise ValueError(f"{self.group_id} is not a VK group")
        return response["object_id"]

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

            items = response["items"]
            if not items:
                break

            for post in items:
                if post["date"] < self.from_ts:
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
                "owner_id": await self._resolve_group_id() * -1,
                "post_id": post_id,
                "count": count,
                "offset": offset,
                "preview_length": 0,
                "sort": "desc",
            })
            await asyncio.sleep(RATE_LIMIT_DELAY)

            items = response["items"]
            if not items:
                break

            for comment in items:
                if comment["date"] < self.from_ts:
                    return comments

                if comment.get("text") and len(comment.get("text")) > 0:
                    comments.append({
                        "text": comment["text"],
                        "date": make_aware(
                            datetime.fromtimestamp(comment["date"])
                        ),
                        "external_id": f'vk_{post_id}_{comment["id"]}',
                    })

            offset += count

        return comments

    async def parse(self):
        posts = await self.fetch_posts_until_date()
        result = []

        for post in posts:
            if post.get("comments", {}).get("count", 0) == 0:
                continue

            post_comments = await self.fetch_comments(post["id"])
            result.extend(post_comments)

        return result
