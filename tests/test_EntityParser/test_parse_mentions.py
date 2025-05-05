from telegram import MessageEntity
from telegram.constants import MessageEntityType

from ptbtest.entityparser import EntityParser


class TestParseMentions:
    ep = EntityParser

    def test_empty_string(self):
        assert self.ep.parse_mentions("") == ()

    def test_text_without_mentions(self):
        text = "Text without any mentions"
        assert self.ep.parse_mentions(text) == ()

    def test_less_than_4_char_in_entity(self):
        # Must ignore mentions with the length less than 4 characters.
        # Only exceptions are @gif, @vid, @pic
        assert self.ep.parse_mentions("@a") == ()
        assert self.ep.parse_mentions("@ab") == ()
        assert self.ep.parse_mentions("@abc") == ()

    def test_more_than_32_chars_in_entity(self):
        assert self.ep.parse_mentions("@" + "a"*33) == ()
        assert self.ep.parse_mentions("@" + "a"*35) == ()
        assert self.ep.parse_mentions("@" + "a"*100) == ()

    def test_4_characters_exactly(self):
        assert self.ep.parse_mentions("@abcd") == (MessageEntity(length=5, offset=0,
                                                                 type=MessageEntityType.MENTION),)
        assert self.ep.parse_mentions("@ab12") == (MessageEntity(length=5, offset=0,
                                                                 type=MessageEntityType.MENTION),)

    def test_32_characters_exactly(self):
        assert self.ep.parse_mentions("@" + "b"*32) == (MessageEntity(length=33, offset=0,
                                                                      type=MessageEntityType.MENTION),)

    def test_allowed_3_chars_mentions(self):
        assert self.ep.parse_mentions("@gif") == (MessageEntity(length=4, offset=0,
                                                                type=MessageEntityType.MENTION),)
        assert self.ep.parse_mentions("@vid") == (MessageEntity(length=4, offset=0,
                                                                type=MessageEntityType.MENTION),)
        assert self.ep.parse_mentions("@pic") == (MessageEntity(length=4, offset=0,
                                                                type=MessageEntityType.MENTION),)

    def test_all_allowed_characters(self):
        assert self.ep.parse_mentions("@user_123") == (MessageEntity(length=9, offset=0,
                                                                type=MessageEntityType.MENTION),)

    def test_underscore_at_the_beginning(self):
        assert self.ep.parse_mentions("@_user") == (MessageEntity(length=6, offset=0,
                                                                  type=MessageEntityType.MENTION),)

    def test_only_digits(self):
        assert self.ep.parse_mentions("@1234567890") == (MessageEntity(length=11, offset=0,
                                                                       type=MessageEntityType.MENTION),)

    def test_multiple_entities(self):
        resp = self.ep.parse_mentions("Hello to @user1 and hello to @user2")

        assert resp == (MessageEntity(length=6, offset=9, type=MessageEntityType.MENTION),
                        MessageEntity(length=6, offset=29, type=MessageEntityType.MENTION))
