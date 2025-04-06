import asyncio

from telegram import Bot, Chat, Update
from telegram.ext import Application

from ptbtest.usergenerator import UserGenerator
from ptbtest_request import MockAPI
from ptbtest_request import PTBRequest


def patch_app(app: Application, bot_fname=None, bot_username=None, bot_id=1):
    """
    Patches configured `Application` instance.
    - adds `User` information to the bot instance
    - creates a `MockAPI` instance
    - creates a `PTBRequest` object
    - replaces the bot's requests objects with `PTBRequest`.
    """
    app.bot._bot_user = UserGenerator().get_user(first_name=bot_fname,
                                                 username=bot_username,
                                                 user_id=bot_id)
    api = MockAPI(app.bot)
    request_obj = PTBRequest(api)
    app.bot._request = (request_obj, request_obj)

    return app, api


class UpdateFeeder:
    """
    This a convenient class to get updates from and to put updates in the update queue
    of the MockAPI.
    Also, the class has convenient methods for putting updates into
    the internal queue.
    """
    def __init__(self, bot: Bot, mock_api: MockAPI):
        self._bot = bot
        self._api = mock_api

    def add_update(self, update: Update):
        """
        right now this method does not much work, but...
        But we can create methods for audio, video, channels, groups.
        `add_video_message`, `add_audio_message`, `add_text_message`, etc.

        And it will explicitly make `Update` from `Message`.
        Because right now it is done implicitly by `MessageGenerator.get_message()`
        and others.
        """
        self._api.put_update(update)

    def add_text_message(self, text: str, chat: Chat = None):
        # ch = chat if chat else ChatGenerator().get_chat()
        # msg = MessageGenerator().get_message(text=text, via_bot=self._bot).message
        # return msg
        pass

    def get_updates(self) -> tuple[Update, ...]:
        return self._api.get_updates()



async def process_updates(app: Application, update_feeder: UpdateFeeder):
    """
    The function is used for processing incoming updates by the application.
    """
    updates = update_feeder.get_updates()
    tasks = list()
    for update in updates:
        tasks.append(asyncio.ensure_future(app.process_update(update)))

    await asyncio.wait(tasks)


