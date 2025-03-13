#!/usr/bin/env python
# pylint: disable=E0611,E0213,E1102,C0103,E1101,W0613,R0913,R0904
#
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
from __future__ import absolute_import
import json

import asyncio
import unittest

import pytest
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import InlineQueryResult
from telegram import User, Message, Chat, Update
from telegram.constants import ChatAction, ParseMode
from telegram.error import TelegramError
from telegram.ext import Updater

from ptbtest import Mockbot


class TestMockbot:
    mockbot = Mockbot()

    # This one is passing, but I believe it's wrong and I don't know why. (c) Eldinnie
    async def test_updater_works_with_mockbot(self):
        # handler method
        def start(bot, update):
            message = bot.sendMessage(update.message.chat_id, "this works")
            assert isinstance(message, Message)

        updater = Updater(bot=self.mockbot, update_queue=asyncio.Queue())
        async with updater:
            user = User(id=1, first_name="test", is_bot=True)
            chat = Chat(45, "group")
            message = Message(
                404, user, None, chat, text="/start", via_bot=self.mockbot)
            message2 = Message(
                404, user, None, chat, text="start", via_bot=self.mockbot)
            message3 = Message(
                404, user, None, chat, text="/start@MockBot", via_bot=self.mockbot)
            message4 = Message(
                404, user, None, chat, text="/start@OtherBot", via_bot=self.mockbot)
            self.mockbot.insertUpdate(Update(0, message=message))
            self.mockbot.insertUpdate(Update(1, message=message2))
            self.mockbot.insertUpdate(Update(1, message=message3))
            self.mockbot.insertUpdate(Update(1, message=message4))
            data = self.mockbot.sent_messages
            assert len(data) == 2
            data = data[0]
            assert data['method'] == 'sendMessage'
            assert data['chat_id'] == chat.id

    def test_properties(self):
        assert self.mockbot.id == 0
        assert self.mockbot.first_name == "Mockbot"
        assert self.mockbot.last_name == "Bot"
        assert self.mockbot.name == "@MockBot"
        mb2 = Mockbot("OtherUsername")
        assert mb2.name == "@OtherUsername"
        self.mockbot.sendMessage(1, "test 1")
        self.mockbot.sendMessage(2, "test 2")
        assert len(self.mockbot.sent_messages) == 2
        self.mockbot.reset()
        assert len(self.mockbot.sent_messages) == 0

    def test_dejson_and_to_dict(self):
        d = self.mockbot.to_dict()
        assert isinstance(d, dict)
        js = json.loads(json.dumps(d))
        b = Mockbot.de_json(js, None)
        assert isinstance(b, Mockbot)

    def test_answerCallbackQuery(self):
        self.mockbot.answerCallbackQuery(
            1, "done", show_alert=True, url="google.com", cache_time=2)

        data = self.mockbot.sent_messages[-1]
        assert data['method'] == "answerCallbackQuery"
        assert data['text'] == "done"

    def test_answerInlineQuery(self):
        r = [
            InlineQueryResult("string", "1"), InlineQueryResult("string", "2")
        ]
        self.mockbot.answerInlineQuery(
            1,
            r,
            is_personal=True,
            next_offset=3,
            switch_pm_parameter="asd",
            switch_pm_text="pm")

        data = self.mockbot.sent_messages[-1]
        assert data['method'] == "answerInlineQuery"
        assert data['results'][0]['id'] == "1"

    def test_editMessageCaption(self):
        self.mockbot.editMessageCaption(chat_id=12, message_id=23)

        data = self.mockbot.sent_messages[-1]
        assert data['method'] == "editMessageCaption"
        assert data['chat_id'] == 12
        self.mockbot.editMessageCaption(
            inline_message_id=23, caption="new cap", photo=True)
        data = self.mockbot.sent_messages[-1]
        assert data['method'] == "editMessageCaption"
        with pytest.raises(TelegramError):
            self.mockbot.editMessageCaption()
        with pytest.raises(TelegramError):
            self.mockbot.editMessageCaption(chat_id=12)
        with pytest.raises(TelegramError):
            self.mockbot.editMessageCaption(message_id=12)

    def test_editMessageReplyMarkup(self):
        self.mockbot.editMessageReplyMarkup(chat_id=1, message_id=1)
        data = self.mockbot.sent_messages[-1]
        assert data['method'] == "editMessageReplyMarkup"
        assert data['chat_id'] == 1

        self.mockbot.editMessageReplyMarkup(inline_message_id=1)
        data = self.mockbot.sent_messages[-1]
        assert data['method'] == "editMessageReplyMarkup"
        assert data['inline_message_id'] == 1

        with pytest.raises(TelegramError):
            self.mockbot.editMessageReplyMarkup()
        with pytest.raises(TelegramError):
            self.mockbot.editMessageReplyMarkup(chat_id=12)
        with pytest.raises(TelegramError):
            self.mockbot.editMessageReplyMarkup(message_id=12)

    def test_editMessageText(self):
        self.mockbot.editMessageText("test", chat_id=1)
        data = self.mockbot.sent_messages[-1]
        assert data['method'] == "editMessageText"
        assert data['chat_id'] == 1
        assert data['text'] == "test"
        self.mockbot.editMessageText(
            "test",
            inline_message_id=1,
            parse_mode="Markdown",
            disable_web_page_preview=True)
        data = self.mockbot.sent_messages[-1]
        assert data['method'] == "editMessageText"
        assert data['inline_message_id'] == 1

    def test_forwardMessage(self):
        self.mockbot.forwardMessage(1, 2, 3)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "forwardMessage"
        assert data['chat_id'] == 1

    def test_getChat(self):
        self.mockbot.getChat(1)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "getChat"
        assert data['chat_id'] == 1

    def test_getChatAdministrators(self):
        self.mockbot.getChatAdministrators(chat_id=2)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "getChatAdministrators"
        assert data['chat_id'] == 2

    def test_getChatMember(self):
        self.mockbot.getChatMember(1, 3)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "getChatMember"
        assert data['chat_id'] == 1
        assert data['user_id'] == 3

    def test_getChatMembersCount(self):
        self.mockbot.getChatMembersCount(1)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "getChatMembersCount"
        assert data['chat_id'] == 1

    def test_getFile(self):
        self.mockbot.getFile("12345")
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "getFile"
        assert data['file_id'] == "12345"

    def test_getGameHighScores(self):
        self.mockbot.getGameHighScores(
            1, chat_id=2, message_id=3, inline_message_id=4)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "getGameHighScores"
        assert data['user_id'] == 1

    def test_getMe(self):
        data = self.mockbot.getMe()

        assert isinstance(data, User)
        assert data.name == "@MockBot"

    def test_getUpdates(self):
        data = self.mockbot.getUpdates()

        assert data == []

    def test_getUserProfilePhotos(self):
        self.mockbot.getUserProfilePhotos(1, offset=2)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "getUserProfilePhotos"
        assert data['user_id'] == 1

    def test_kickChatMember(self):
        self.mockbot.kickChatMember(chat_id=1, user_id=2)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "kickChatMember"
        assert data['user_id'] == 2

    def test_leaveChat(self):
        self.mockbot.leaveChat(1)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "leaveChat"

    def test_sendAudio(self):
        self.mockbot.sendAudio(
            1,
            "123",
            "audio_unique_id",
            duration=2,
            performer="singer",
            title="song",
            caption="this song")
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "sendAudio"
        assert data['chat_id'] == 1
        assert data['duration'] == 2
        assert data['performer'] == "singer"
        assert data['title'] == "song"
        assert data['caption'] == "this song"

    def test_sendChatAction(self):
        self.mockbot.sendChatAction(1, ChatAction.TYPING)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "sendChatAction"
        assert data['chat_id'] == 1
        assert data['action'] == "typing"

    def test_sendContact(self):
        self.mockbot.sendContact(1, "123456", "test", last_name="me")
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "sendContact"
        assert data['chat_id'] == 1
        assert data['phone_number'] == "123456"
        assert data['last_name'] == "me"

    def test_sendDocument(self):
        self.mockbot.sendDocument(
            1, "45", "document_unique_id", filename="jaja.docx", caption="good doc")
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "sendDocument"
        assert data['chat_id'] == 1
        assert data['filename'] == "jaja.docx"
        assert data['caption'] == "good doc"

    def test_sendGame(self):
        self.mockbot.sendGame(1, "testgame")
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "sendGame"
        assert data['chat_id'] == 1
        assert data['game_short_name'] == "testgame"

    def test_sendLocation(self):
        self.mockbot.sendLocation(1, 52.123, 4.23)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "sendLocation"
        assert data['chat_id'] == 1

    def test_sendMessage(self):
        keyb = InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                "test 1", callback_data="test1")],
             [InlineKeyboardButton(
                 "test 2", callback_data="test2")]])
        self.mockbot.sendMessage(
            1,
            "test",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyb,
            disable_notification=True,
            reply_to_message_id=334,
            disable_web_page_preview=True)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "sendMessage"
        assert data['chat_id'] == 1
        assert data['text'] == "test"
        assert eval(data['reply_markup'])['inline_keyboard'][1][0]['callback_data'] == "test2"

    def test_sendPhoto(self):
        self.mockbot.sendPhoto(1, "test.png", caption="photo")
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "sendPhoto"
        assert data['chat_id'] == 1
        assert data['caption'] == "photo"

    def test_sendSticker(self):
        self.mockbot.sendSticker(-4231, "test", "sticker_unique_id", 10, 10, True, True, "regular")
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "sendSticker"
        assert data['chat_id'] == -4231

    def test_sendVenue(self):
        self.mockbot.sendVenue(
            1, 4.2, 5.1, "nice place", "somewherestreet 2", foursquare_id=2)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "sendVenue"
        assert data['chat_id'] == 1
        assert data['foursquare_id'] == 2

    def test_sendVideo(self):
        self.mockbot.sendVideo(1, "some file", "video_unique_id", 10, 10, 3)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "sendVideo"
        assert data['chat_id'] == 1
        assert data['video2']['width'] == 10
        assert data['video2']['height'] == 10
        assert data['video2']['duration'] == 3

    def test_sendVoice(self):
        self.mockbot.sendVoice(1, "some file", "voide_unique_id", duration=3, caption="voice")
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "sendVoice"
        assert data['chat_id'] == 1
        assert data['duration'] == 3
        assert data['caption'] == "voice"

    def test_setGameScore(self):
        self.mockbot.setGameScore(
            1,
            200,
            chat_id=2,
            message_id=3,
            inline_message_id=4,
            force=True,
            disable_edit_message=True)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "setGameScore"
        assert data['user_id'] == 1
        self.mockbot.setGameScore(1, 200, edit_message=True)

    def test_unbanChatMember(self):
        self.mockbot.unbanChatMember(1, 2)
        data = self.mockbot.sent_messages[-1]

        assert data['method'] == "unbanChatMember"
        assert data['chat_id'] == 1
