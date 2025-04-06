import asyncio

from telegram import Bot, Update, Chat
from telegram.ext import Application

from ptbtest_request import MockAPI, PTBRequest
from ptbtest import MessageGenerator, ChatGenerator
from ptbtest.usergenerator import UserGenerator


class MockApplication:
    def __init__(self, app: Application,
                 bot_fname: str = None,
                 bot_username: str = None,
                 bot_id: int = None):
        self._app: Application = app
        self._bot: Bot = app.bot
        self._api = MockAPI(self._bot)

        request_obj = PTBRequest(self._api)
        self._bot._request = (request_obj, request_obj)

        self._init(bot_fname, bot_username, bot_id)

    def _init(self, bot_fname: str = None, bot_username: str = None, bot_id: int = None):
        user = UserGenerator().get_user(first_name=bot_fname, username=bot_username,
                                        user_id=bot_id, is_bot=True)
        self._bot._bot_user = user

    async def __aenter__(self):
        await self._app.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._app.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def incoming_updates(self):
        return self._api.incoming_updates

    @property
    def sent_messages(self):
        return self._api.sent_messages

    @property
    def last_sent_message(self):
        return self._api.last_sent_message

    def clear_sent_messages(self):
        self._api.sent_messages.clear()

    def add_update(self, update: Update):
        """
        right now this method does not do much work, but...
        we could create methods for audio, video, channels, groups.
        `add_video_message`, `add_audio_message`, `add_text_message`, etc.

        And it will explicitly make `Update` from `Message`.
        Because right now it is done implicitly by `MessageGenerator.get_message()`
        and others.
        """
        self._api.put_update(update)

    def send_private_message(self, text, chat_id):
        chat = ChatGenerator().get_chat(chat_id)
        msg = MessageGenerator(self._bot).get_message(text=text, chat=chat)

        self.add_update(msg)

    def get_updates(self) -> tuple[Update, ...]:
        return self._api.get_updates()

    async def process_updates(self):
        """
        The function is used for processing incoming updates by the application.
        """
        tasks = list()
        for update in self.get_updates():
            tasks.append(asyncio.ensure_future(self._app.process_update(update)))

        await asyncio.wait(tasks)