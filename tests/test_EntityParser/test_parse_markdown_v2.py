import re

import pytest
from telegram.constants import MessageEntityType

from ptbtest.entityparser import EntityParser
from ptbtest.errors import BadMarkupException

ERR_MSG_CANT_PARSE_ENTITY = ("Can't parse entities: can't find end of {entity_type}"
                             " entity at byte offset {offset}")

ERR_MSG_EMPTY_STR = "Message text is empty"

ERR_MSG_CHAR_MUST_BE_ESCAPED = ("Can't parse entities: character '{0}' is reserved"
                                " and must be escaped with the preceding '\\'")

RESERVED_REGULAR_CHARS = "]()>#+=-|{}.!"
# There are two more entity chars which are "```" and "||",
# but I wrote personalized tests for them.
RESERVED_ENTITY_CHARS = "_*~`"


class TestNoEntities:
    ep = EntityParser()
    def test_empty_string(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_EMPTY_STR):
            self.ep.parse_markdown_v2("")

    def test_single_line_text(self):
        resp = self.ep.parse_markdown_v2("A single line text")
        assert resp == ("A single line text", ())

    def test_multiline_string(self):
        resp = self.ep.parse_markdown_v2("A string\non three\nlines")
        assert resp == ("A string\non three\nlines", ())

    def test_multiline_string_with_leading_and_trailing_whitespaces(self):
        resp = self.ep.parse_markdown_v2("   A multiline\nstring\nwith leading and\ntrailing \nwhitespaces     ")
        assert resp == ("A multiline\nstring\nwith leading and\ntrailing \nwhitespaces", ())

    def test_multiline_string_with_leading_and_trailing_newlines(self):
        resp = self.ep.parse_markdown_v2("\n\n \nA multiline\nstring\nwith leading and\ntrailing \nnewlines \n  \n")
        assert resp == ("A multiline\nstring\nwith leading and\ntrailing \nnewlines", ())


class TestEscaping:
    ep = EntityParser()

    @pytest.mark.parametrize(["char"], RESERVED_REGULAR_CHARS)
    def test_escaped_reserved_regular_characters(self, char):
        template = "A string with an escaped \{0} character"
        resp = self.ep.parse_markdown_v2(template.format(char))
        assert resp == (f"A string with an escaped {char} character", ())

    @pytest.mark.parametrize(["char"], RESERVED_ENTITY_CHARS + RESERVED_REGULAR_CHARS)
    def test_escaped_reserved_characters(self, char):
        template = "A string with an escaped \{0} character"
        resp = self.ep.parse_markdown_v2(template.format(char))
        assert resp == (f"A string with an escaped {char} character", ())

    def test_pre_entity_escaped_only_first_char(self):
        resp = self.ep.parse_markdown_v2(f"A string with an escaped \``` character")
        assert resp == ('A string with an escaped ` character', ())

    def test_escaped_pre_entity(self):
        resp = self.ep.parse_markdown_v2(f"A string with an escaped \`\`\` character")
        assert resp == ('A string with an escaped ``` character', ())

    def test_escaped_spoiler_entity(self):
        resp = self.ep.parse_markdown_v2(f"A string with an escaped \|\| character")
        assert resp == ('A string with an escaped || character', ())

    def test_spoiler_entity_escaped_only_first_char(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CHAR_MUST_BE_ESCAPED.format(r"|")):
            self.ep.parse_markdown_v2("A string with an escaped \|| character")

    @pytest.mark.parametrize(["char"], RESERVED_REGULAR_CHARS)
    def test_unescaped_regular_characters(self, char):
        template = "A string with an unescaped {0} character"
        with pytest.raises(BadMarkupException, match=re.escape(ERR_MSG_CHAR_MUST_BE_ESCAPED.format(char))):
            self.ep.parse_markdown_v2(template.format(char))

    def test_unescaped_pre(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CANT_PARSE_ENTITY.format(
            entity_type=MessageEntityType.PRE, offset=14
        )):
            self.ep.parse_markdown_v2("A string with ```")

    def test_unescaped_spoiler(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CANT_PARSE_ENTITY.format(
            entity_type=MessageEntityType.SPOILER, offset=14
        )):
            self.ep.parse_markdown_v2("A string with ||")

    def test_spoiler_with_first_escaped_symbol(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CHAR_MUST_BE_ESCAPED.format("|")):
            self.ep.parse_markdown_v2("A string with \||")

    def test_spoiler_with_second_escaped_symbol(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CHAR_MUST_BE_ESCAPED.format("|")):
            self.ep.parse_markdown_v2("A string with |\|")

