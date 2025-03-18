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
"""This module provides a class to generate telegram chats"""
import random
from typing import Optional, Union

from telegram import Chat, User
from telegram.constants import ChatType

from ptbtest import UserGenerator
from ptbtest.ptbgenerator import PtbGenerator


class ChatGenerator(PtbGenerator):
    """
        Chat generator class. Placeholder for random names and mainly used
        via it's get_chat() method.
    """
    GROUPNAMES = (
        "Frustrated Vagabonds", "Heir Apparents", "Walky Talky",
        "Flirty Crowns", "My Amigos"
    )

    def __init__(self):
        super().__init__()

    def get_chat(self,
                 cid: Optional[int] = None,
                 chat_type: Union[ChatType, str] = ChatType.PRIVATE,
                 title: Optional[str] = None,
                 username: Optional[str] = None,
                 user: Optional[User] = None,
                 is_forum: bool = False,
                 *,
                 all_members_are_administrators: bool = False) -> Chat:
        """
        Returns a telegram.Chat object with the optionally given type or username
        If any of the arguments are omitted the names will be chosen randomly and the
        username will be generated as first_name + last_name.

        When called without arguments will return a telegram.Chat object for a private chat with a randomly
        generated user.

        Args:
            cid (Optional[int]): ID of the returned chat.
            chat_type (Union[ChatType, str]): Type of the chat can be either
                telegram.constants.ChatType or the string literal ("private", "group", "supergroup", "channel").
            title (Optional[str]): Title  for the group/supergroup/channel.
            username (Optional[str]): Username for the private/supergroup/channel.
            user (Optional[telegram.User]): If given, a private chat for the supplied user will be generated.
            is_forum (bool): True, if the supergroup chat is a forum (has topics enabled)
            all_members_are_administrators (Optional[bool]): Sets this flag for a group.

        Returns:
            telegram.Chat: A telegram Chat object.
        """
        if cid:
            if cid < 0 and chat_type not in (ChatType.GROUP, ChatType.SUPERGROUP):
                raise ValueError("Only groups and supergroups can have the negative 'cid'")
            elif cid > 0 and chat_type not in (ChatType.PRIVATE, ChatType.CHANNEL):
                raise ValueError("Only private chats and channels can have the positive 'cid'")

        if is_forum and chat_type not in (ChatType.GROUP, ChatType.SUPERGROUP):
            raise ValueError("'is_forum' can be True for groups and supergroups only")

        if user or chat_type == ChatType.PRIVATE:
            if user and not isinstance(user, User):
                raise TypeError("user must be a telegram.User instance")

            u = user if user else UserGenerator().get_user(username=username)

            return Chat(
                cid or u.id,
                chat_type,
                username=u.username,
                first_name=u.first_name,
                last_name=u.last_name,
                is_forum=is_forum)

        elif chat_type in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL):
            gn = title if title else random.choice(self.GROUPNAMES) # noqa: S311
            if not username and chat_type != ChatType.GROUP:
                username = "".join(gn.split(" "))

            return Chat(
                cid or self.gen_id(group=True),
                chat_type,
                title=gn,
                username=username,
                is_forum=is_forum,
                api_kwargs={"all_members_are_administrators": all_members_are_administrators})

