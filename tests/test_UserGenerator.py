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

from ptbtest import UserGenerator


@pytest.fixture(scope="function")
def mock_user():
    return UserGenerator()

class TestUserGenerator:
    def test_no_specification(self, mock_user):
        u = mock_user.get_user()
        assert isinstance(u.id, int)
        assert u.id > 0
        assert isinstance(u.first_name, str)
        assert u.username == u.first_name + u.last_name

    def test_with_first_name(self, mock_user):
        u = mock_user.get_user(first_name="Test")
        assert u.first_name == "Test"
        assert u.first_name.startswith("Test")

    def test_with_username(self, mock_user):
        u = mock_user.get_user(username="misterbot")
        assert u.username == "misterbot"
        assert u.full_name != u.username

    def test_compare_users(self, mock_user):
        a = mock_user.get_user()
        b = mock_user.get_user()
        assert a != b
        assert a.id != b.id

    def test_compare_users_with_same_names(self, mock_user):
        a = mock_user.get_user(first_name="same", last_name="names")
        b = mock_user.get_user(first_name="same", last_name="names")
        assert a != b
        assert a.id != b.id

    def test_compare_same_user_with_different_names(self, mock_user):
        a = mock_user.get_user(user_id=1)
        b = mock_user.get_user(user_id=1)
        assert a == b
        assert a.id == b.id
        assert a.username != b.username
