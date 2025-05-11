from telegram import MessageEntity
from telegram.constants import MessageEntityType

from ptbtest.entityparser import EntityParser


class TestParseCashtags:
    ep = EntityParser()

    def test_empty_string(self):
        assert self.ep.parse_cashtags("") == ()

    def test_without_cash_tags(self):
        assert self.ep.parse_cashtags("Hello @durov") == ()

    def test_1INCH(self):
        result = self.ep.parse_cashtags("$1INCH")

        assert result == (MessageEntity(length=6, offset=0, type=MessageEntityType.CASHTAG), )

    def test_one_char_cash_tag(self):
        result = self.ep.parse_cashtags("$A")

        assert result == (MessageEntity(length=2, offset=0, type=MessageEntityType.CASHTAG), )

    def test_multiple_cash_tags(self):
        result = self.ep.parse_cashtags("$HELLO $WORLD")

        assert result == (MessageEntity(length=6, offset=0, type=MessageEntityType.CASHTAG),
                          MessageEntity(length=6, offset=7, type=MessageEntityType.CASHTAG))

    def test_max_length__8_symbols(self):
        result = self.ep.parse_cashtags("$ABCDEFGH")

        assert result == (MessageEntity(length=9, offset=0, type=MessageEntityType.CASHTAG),)

    def test_more_than_max_length__9_symbols(self):
        result = self.ep.parse_cashtags("$QWERTYUIY")

        assert result == ()

    def test_non_ascii_letters(self):
        assert self.ep.parse_cashtags("$河") == ()
        assert self.ep.parse_cashtags("$ФЖМ") == ()

    def test_with_mention(self):
        text = "$ZXC@mention"

        result = self.ep.parse_cashtags(text)

        assert result == (MessageEntity(length=12, offset=0, type=MessageEntityType.CASHTAG),)

    def test_with_too_small_mention_up_to_3_chars(self):
        expected = (MessageEntity(length=5, offset=0, type=MessageEntityType.CASHTAG),)

        assert self.ep.parse_cashtags("$ABCD@") == expected
        assert self.ep.parse_cashtags("$EFGH@a") == expected
        assert self.ep.parse_cashtags("$IJKL@ab") == expected
        assert self.ep.parse_cashtags("$MNOP@a-b") == expected

    def test_with_max_allowed_length_mention__32_chars(self):
        text = "$CVB@" + "a" * 32

        result = self.ep.parse_cashtags(text)

        assert result == (MessageEntity(length=37, offset=0, type=MessageEntityType.CASHTAG),)

    def test_with_too_long_mention__33_chars(self):
        text = "$CVB@" + "a" * 33

        result = self.ep.parse_cashtags(text)

        assert result == (MessageEntity(length=4, offset=0, type=MessageEntityType.CASHTAG),)

    def test_with_mention_and_with_dollar_sign_at_the_end_of_mention(self):
        text = "$NKP@username$"

        result = self.ep.parse_cashtags(text)

        assert result == (MessageEntity(length=4, offset=0, type=MessageEntityType.CASHTAG),)

    def test_string_with_dollar_signs_only(self):
        assert self.ep.parse_cashtags("$") == ()
        assert self.ep.parse_cashtags("$$$") == ()
        assert self.ep.parse_cashtags("$$$$$$$") == ()

    def test_cashtag_with_trailing_dollar_sign(self):
        assert self.ep.parse_cashtags("$UUU$") == ()
        assert self.ep.parse_cashtags("$UUU$@mention") == ()

    def test_whitespace_between_hash_sign_and_word(self):
        assert self.ep.parse_cashtags("$ ABC") == ()
        assert self.ep.parse_cashtags("ABC$ DEF") == ()

    def test_dollar_sign_in_the_middle_of_string(self):
        assert self.ep.parse_cashtags("ABC$DEF") == ()
        assert self.ep.parse_cashtags("Ж$DEF") == ()

    def test_digits_in_cashtag(self):
        assert self.ep.parse_cashtags("$1234") == ()
        assert self.ep.parse_cashtags("$ABC12") == ()

    def test_mixed_cases(self):
        assert self.ep.parse_cashtags("$abc") == ()
        assert self.ep.parse_cashtags("$ABc") == ()
        assert self.ep.parse_cashtags("$AbCdE") == ()

    def test_utf16_offset(self):
        result = self.ep.parse_cashtags("😄😄😄😄 😄😄😄$ABC")

        assert result == (MessageEntity(length=4, offset=15, type=MessageEntityType.CASHTAG),)
