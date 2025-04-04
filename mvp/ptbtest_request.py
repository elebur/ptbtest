import json
from pprint import pprint
from typing import Optional

from telegram import Bot, Chat, User, Update, Message
from telegram._utils.defaultvalue import DEFAULT_NONE
from telegram._utils.types import ODVInput
from telegram.request import BaseRequest, RequestData

from ptbtest.messagegenerator import MessageGenerator


class MockAPI:
    """
    The class emulating the Telegram API.
    """
    def __init__(self, bot: Bot):
        self._bot = bot
        self._msg_gen = MessageGenerator()
        # All messages sent by the bot
        self._sent_messages: list[Message] = list()
        # The Telegram API returns info about a chat and a user
        # when a bot sends a message to the user.
        # We cannot get this information from the servers, so we'll
        # save it from incoming updates and add this information
        # to outgoing messages.
        self._known_chats: dict[int, Chat] = dict()
        self._known_users: dict[int, User] = dict()
        # Updates from users.
        self._incoming_updates: list[Update] = list()

        self._endpoints = {
            "getMe": self._get_me,
            "deleteWebhook": self._delete_web_hook,
            "getUpdates": self._get_updates_api,
            "sendMessage": self._send_message
        }

    def __call__(self, endpoint: str, request_data: RequestData, *args, **kwargs) -> tuple[int, bytes]:
        response = self._endpoints[endpoint](request_data)
        # This is a response format expected by the bot.
        return 200, (json.dumps({"ok": True, "result": response})).encode()

    @property
    def sent_messages(self):
        return self._sent_messages

    @property
    def last_message(self):
        return self._sent_messages[-1]

    def clear_sent_messages(self):
        self._sent_messages.clear()

    def put_update(self, update: Update):
        """
        Puts an update into internal queue.
        """
        print("put update".center(80, "-"))
        print(update)
        chat = update.message.chat
        user = update.message.from_user

        if chat and chat.id not in self._known_chats:
            self._known_chats[chat.id] = chat

        if user and user.id not in self._known_users:
            self._known_users[user.id] = user

        self._incoming_updates.append(update)

    def get_updates(self) -> tuple[Update, ...]:
        """
        Returns all available updates.
        """
        cp_updates = self._incoming_updates.copy()
        self._incoming_updates.clear()
        return tuple(cp_updates)

    def _get_me(self, request_data) -> str:
        return self._bot._bot_user.to_dict()

    def _get_updates_api(self, offset=None, limit=100, timeout=0, allowed_updates=None):
        raise NotImplemented

    def _delete_web_hook(self, request_data):
        return True

    def _send_message(self, request_data: RequestData):
        pprint(request_data.parameters)
        params = request_data.parameters
        chat_id = params["chat_id"]
        text = params["text"]

        m = self._msg_gen.get_message(chat=self._known_chats.get(chat_id, None),
                                      user=self._bot._bot_user,
                                      text=text).message
        self._sent_messages.append(m)
        return m.to_dict()


class PTBRequest(BaseRequest):

    def __init__(self, bot: Bot, api: MockAPI):
        self._bot = bot
        self._api = api

    async def do_request(self, url: str, method: str, request_data: Optional[RequestData] = None,
                         read_timeout: ODVInput[float] = DEFAULT_NONE, write_timeout: ODVInput[float] = DEFAULT_NONE,
                         connect_timeout: ODVInput[float] = DEFAULT_NONE,
                         pool_timeout: ODVInput[float] = DEFAULT_NONE) -> tuple[int, bytes]:
        print(f"{url=}")
        endpoint = url.split("/")[-1]
        return self._api(endpoint, request_data)

    @property
    def read_timeout(self) -> Optional[float]:
        return 1

    async def initialize(self) -> None:
        print("initialize")

    async def shutdown(self) -> None:
        print("shutdown")
