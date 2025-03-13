# A library that provides a testing suite fot python-telegram-bot
# wich can be found on https://github.com/python-telegram-bot/python-telegram-bot
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

from ptbtest import UserGenerator


class TestUserGenerator:
    def test_no_specification(self):
        u = UserGenerator().get_user()
        assert isinstance(u.id, int)
        assert u.id > 0
        assert isinstance(u.first_name, str)
        assert u.username == u.first_name + u.last_name

    def test_with_first_name(self):
        u = UserGenerator().get_user(first_name="Test")
        assert u.first_name == "Test"
        assert u.username.startswith("Test")

    def test_with_username(self):
        u = UserGenerator().get_user(username="misterbot")

        assert u.username == "misterbot"
