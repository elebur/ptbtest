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
import pytest

from ptbtest import ChatGenerator, UserGenerator


@pytest.fixture(scope="function")
def mock_chat():
    return ChatGenerator()


class TestChatGenerator:
    def test_without_parameters(self, mock_chat):
        c = mock_chat.get_chat()

        assert isinstance(c.id, int)
        assert c.id > 0
        assert c.type == "private"
        assert c.username == c.first_name + c.last_name

    def test_cid_only(self, mock_chat):
        c = mock_chat.get_chat(cid=1)

        assert c.type == "private"
        assert c.username == c.first_name + c.last_name

        c = mock_chat.get_chat(cid=-1)

        assert c.type == "group"
        assert c.first_name is None
        assert c.last_name is None

    def test_invalid_cid(self, mock_chat):
        c = mock_chat.get_chat(cid=0)

        assert c.id > 0
        assert c.type == "private"
        assert c.username == c.first_name + c.last_name

    def test_with_cid_and_private(self, mock_chat):
        """If cid conflicts with chat_type, cid wins"""
        c = mock_chat.get_chat(chat_type="private", cid=-1)
        assert c.id == -1
        assert c.type == "group"

    def test_with_cid_not_private(self, mock_chat):
        c = mock_chat.get_chat(chat_type="group", cid=-1)
        assert c.type == "group"

        c = mock_chat.get_chat(chat_type="supergroup", cid=-1)
        assert c.type == "supergroup"

        c = mock_chat.get_chat(chat_type="channel", cid=-1)
        assert c.type == "channel"

    def test_group_chat(self):
        c = ChatGenerator().get_chat(chat_type="group")

        assert c.id < 0
        assert c.type == "group"
        assert c.api_kwargs.get("all_members_are_administrators") is False
        assert isinstance(c.title, str)

    def test_group_all_members_are_administrators(self):
        c = ChatGenerator().get_chat(chat_type="group", all_members_are_administrators=True)

        assert c.type == "group"
        assert c.api_kwargs.get("all_members_are_administrators") is True

    def test_group_chat_with_group_name(self):
        c = ChatGenerator().get_chat(chat_type="group", title="My Group")

        assert c.title == "My Group"

    def test_private_from_user(self):
        u = UserGenerator().get_user()
        c = ChatGenerator().get_chat(user=u)

        assert u.id == c.id
        assert c.username == c.first_name + c.last_name
        assert u.username == c.username
        assert c.type == "private"

    def test_supergroup(self):
        c = ChatGenerator().get_chat(chat_type="supergroup")

        assert c.id < 0
        assert c.type == "supergroup"
        assert isinstance(c.title, str)
        assert c.username == "".join(c.title.split())

    def test_supergroup_with_title(self):
        c = ChatGenerator().get_chat(chat_type="supergroup", title="Awesome Group")

        assert c.title == "Awesome Group"
        assert c.username == "AwesomeGroup"

    def test_supergroup_with_username(self):
        c = ChatGenerator().get_chat(chat_type="supergroup", username="mygroup")

        assert c.username == "mygroup"

    def test_supergroup_with_username_title(self):
        c = ChatGenerator().get_chat(
            chat_type="supergroup", username="mygroup", title="Awesome Group")

        assert c.title == "Awesome Group"
        assert  c.username == "mygroup"

    def test_channel(self):
        c = ChatGenerator().get_chat(chat_type="channel")

        assert isinstance(c.title, str)
        assert c.type == "channel"
        assert c.username == "".join(c.title.split())

    def test_channel_with_title(self):
        c = ChatGenerator().get_chat(chat_type="channel", title="Awesome Group")

        assert c.title == "Awesome Group"
        assert c.username == "AwesomeGroup"
