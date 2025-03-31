# A library that provides a testing suite fot python-telegram-bot
# which can be found on https://github.com/python-telegram-bot/python-telegram-bot
# Copyright (C) 2017
# Pieter Schutz - https://github.com/eldinnie
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
"""This module provides a class to generate Telegram callback queries."""

import uuid

from telegram import CallbackQuery, Message, User

from ptbtest import ChatGenerator, MessageGenerator, Mockbot, UserGenerator
from ptbtest.errors import BadBotException, BadCallbackQueryException, BadMessageException, BadUserException
from ptbtest.ptbgenerator import PtbGenerator
from ptbtest.updategenerator import update


class CallbackQueryGenerator(PtbGenerator):
    """
    Callback query generator class.

    Attributes:
        bot (ptbtest.Mockbot): Bot to encode with the messages

    Paramaters:
        bot (Optional[ptbtest.Mockbot]): supply your own for a custom botname
    """

    def __init__(self, bot=None):
        """Initialize the callback query generator, with an optional bot."""
        PtbGenerator.__init__(self)
        self.ug = UserGenerator()
        if not bot:
            self.bot = Mockbot()
        elif isinstance(bot, Mockbot):
            self.bot = bot
        else:
            raise BadBotException

    @update("callback_query")
    def get_callback_query(
        self,
        user=None,
        chat_instance=None,
        message=None,
        data=None,
        inline_message_id=None,
        game_short_name=None
    ):
        """
        Returns a telegram.Update object containing a callback_query.

        Notes:
            One of *message* and *inline_message_id* must be present.
            One of *data* and *game_short_name* must be present.

        Arguments:
            user (Optional[telegram.User]): User that initiated the callback_query.
            chat_instance (Optional[str]): unique identifier, not used.
            message (Optional[telegram.Message]): Message the callback_query button belongs to.
            data (Optional[string]): Data attached to the button.
            inline_message_id (Optional[str]): Message the callback_query button belongs to.
            game_short_name (Optional[str]): game identifier with this button.

        Returns:
            telegram.Update: containing a :py:class:`telegram.CallbackQuery`
        """
        # Required
        if user:
            if not isinstance(user, User):
                raise BadUserException
        else:
            user = self.ug.get_user()
        if not chat_instance:
            chat_instance = self._gen_id()

        if message:
            if isinstance(message, Message):
                pass
            elif isinstance(message, bool):
                chat = ChatGenerator().get_chat(user=user)
                message = (
                    MessageGenerator().get_message(user=self.bot.get_me(), chat=chat, via_bot=self.bot.get_me()).message
                )
            else:
                raise BadMessageException
        if inline_message_id:
            if isinstance(inline_message_id, str):
                pass
            elif isinstance(inline_message_id, bool):
                inline_message_id = self._gen_id()
            else:
                msg = "inline_message_id should be string or True"
                raise BadCallbackQueryException(msg)

        if len([x for x in [message, inline_message_id] if x]) != 1:
            msg = "exactly 1 of message and inline_message_id is needed"
            raise BadCallbackQueryException(msg)

        if len([x for x in [data, game_short_name] if x]) != 1:
            msg = "exactly 1 of data and game_short_name is needed"
            raise BadCallbackQueryException(msg)

        return CallbackQuery(
            self._gen_id(),
            user,
            chat_instance,
            message=message,
            data=data,
            inline_message_id=inline_message_id,
            game_short_name=game_short_name,
        )

    def _gen_id(self):
        return str(uuid.uuid4())
