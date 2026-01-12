import asyncio
from datetime import datetime

from django.conf import settings
from telethon import TelegramClient
from telethon.tl.types import Channel


class TelegramCommentsParser:
    def __init__(self):
        self.api_id = settings.TELEGRAM_API_ID
        self.api_hash = settings.TELEGRAM_API_HASH
        self.comments_data = []

    async def _get_channel_entity(self, client, channel_username):
        channel = await client.get_entity(channel_username)
        if not isinstance(channel, Channel):
            raise ValueError("Object is not a channel")
        return channel

    async def _process_message_thread(self, client, channel, message, since_dt):
        async for comment in client.iter_messages(
            channel,
            reply_to=message.id,
            reverse=True,
        ):
            if not comment.text:
                continue

            if since_dt and comment.date <= since_dt:
                return

            self.comments_data.append({
                "text": comment.text.strip(),
                "date": comment.date,
            })

    async def collect_comments(self, channel_username: str, since_dt: datetime | None):
        self.comments_data = []

        async with TelegramClient(
            session="django_telegram_session",
            api_id=self.api_id,
            api_hash=self.api_hash,
        ) as client:

            channel = await self._get_channel_entity(client, channel_username)

            async for message in client.iter_messages(
                channel,
                offset_date=since_dt,
                reverse=True,
            ):
                if message.replies and message.replies.replies > 0:
                    await self._process_message_thread(
                        client,
                        channel,
                        message,
                        since_dt,
                    )

        return self.comments_data


parser = TelegramCommentsParser()

def parse_telegram_comments(channel_username: str, since_dt=None):
    return asyncio.run(
        parser.collect_comments(channel_username, since_dt)
    )
