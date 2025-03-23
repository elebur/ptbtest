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
"""This module provides a class to generate telegram users"""
import random
from typing import Optional

from ptbtest.ptbgenerator import PtbGenerator
from telegram import User


class UserGenerator(PtbGenerator):
    """User generator class. Placeholder for random names and mainly used
        via its get_user() method."""
    FIRST_NAMES = (
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
        "Elizabeth", "William", "Linda", "David", "Barbara", "Richard",
        "Susan", "Joseph", "Jessica", "Thomas", "Margaret", "Charles", "Sarah"
    )
    LAST_NAMES = (
        "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller",
        "Wilson", "Moore", "Taylor"
    )

    def __init__(self):
        """Initialize the user generator."""
        super().__init__()

    def get_user(self,
                 first_name: Optional[str] = None,
                 last_name: Optional[str] = None,
                 username: Optional[str] = None,
                 user_id: Optional[int] = None) -> User:
        """
        Returns a telegram.User object with the optionally given name(s) or username.
        If any of the arguments are omitted the names will be chosen randomly and the
        username will be generated as first_name + last_name.

        Args:
            first_name (Optional[str]): First name for the returned user.
            last_name (Optional[str]): Last name for the returned user.
            username (Optional[str]): Username for the returned user.
            user_id (Optional[int]): Id for the returned user.

        Returns:
            telegram.User: A telegram user object

        """
        if not first_name:
            first_name = random.choice(self.FIRST_NAMES)
        if not last_name:
            last_name = random.choice(self.LAST_NAMES)
        if not username:
            username = first_name + last_name
        return User(
            user_id or self.gen_id(),
            first_name,
            False,
            last_name=last_name,
            username=username)

