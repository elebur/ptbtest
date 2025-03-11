#!/usr/bin/env python
# pylint: disable=E0611,E0213,E1102,C0103,E1101,W0613,R0913,R0904
#
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
from __future__ import absolute_import

from ptbtest import ChatGenerator
from ptbtest import UserGenerator


class TestChatGenerator:
    cg = ChatGenerator()

    def test_without_parameters(self):
        c = self.cg.get_chat()

        assert isinstance(c.id, int)
        assert c.id > 0
        assert c.username == c.first_name + c.last_name
        assert c.type == "private"

    def test_group_chat(self):
        c = self.cg.get_chat(type="group")

        assert c.id < 0
        assert c.type == "group"
        assert c.api_kwargs.get("all_members_are_administrators") is False
        assert isinstance(c.title, str)

    def test_group_all_members_are_administrators(self):
        c = self.cg.get_chat(type="group", all_members_are_administrators=True)

        assert c.type == "group"
        assert c.api_kwargs.get("all_members_are_administrators") is True

    def test_group_chat_with_group_name(self):
        c = self.cg.get_chat(type="group", title="My Group")

        assert c.title == "My Group"

    def test_private_from_user(self):
        u = UserGenerator().get_user()
        c = self.cg.get_chat(user=u)

        assert u.id == c.id
        assert c.username == c.first_name + c.last_name
        assert u.username == c.username
        assert c.type == "private"

    def test_supergroup(self):
        c = self.cg.get_chat(type="supergroup")

        assert c.id < 0
        assert c.type == "supergroup"
        assert isinstance(c.title, str)
        assert c.username == "".join(c.title.split())

    def test_supergroup_with_title(self):
        c = self.cg.get_chat(type="supergroup", title="Awesome Group")

        assert c.title == "Awesome Group"
        assert c.username == "AwesomeGroup"

    def test_supergroup_with_username(self):
        c = self.cg.get_chat(type="supergroup", username="mygroup")

        assert c.username == "mygroup"

    def test_supergroup_with_username_title(self):
        c = self.cg.get_chat(
            type="supergroup", username="mygroup", title="Awesome Group")

        assert c.title == "Awesome Group"
        assert  c.username == "mygroup"

    def test_channel(self):
        c = self.cg.get_chat(type="channel")

        assert isinstance(c.title, str)
        assert c.type == "channel"
        assert c.username == "".join(c.title.split())

    def test_channel_with_title(self):
        c = self.cg.get_chat(type="channel", title="Awesome Group")

        assert c.title == "Awesome Group"
        assert c.username == "AwesomeGroup"
