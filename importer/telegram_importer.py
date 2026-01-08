import asyncio

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
            raise ValueError("Указанный объект не является каналом")
        return channel

    async def _process_message_thread(self, client, channel, message):
        async for comment in client.iter_messages(
            channel,
            reply_to=message.id,
            limit=100
        ):
            if comment.text and comment.text.strip():
                self.comments_data.append({
                    "text": comment.text.strip(),
                    "date": comment.date.strftime("%Y-%m-%d %H:%M:%S")
                })

    async def collect_comments(self, channel_username: str):
        self.comments_data = []

        async with TelegramClient(
            session="django_telegram_session",
            api_id=self.api_id,
            api_hash=self.api_hash,
        ) as client:

            channel = await self._get_channel_entity(client, channel_username)

            async for message in client.iter_messages(channel):
                if message.replies and message.replies.replies > 0:
                    await self._process_message_thread(client, channel, message)

        return self.comments_data


parser = TelegramCommentsParser()

def parse_telegram_comments(channel_username: str):
    return asyncio.run(parser.collect_comments(channel_username))
