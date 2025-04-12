import re
from re import match

import pytest
from markdown_it.rules_inline import entity
from telegram import MessageEntity
from telegram.constants import MessageEntityType

from ptbtest.entityparser import EntityParser
from ptbtest.errors import BadMarkupException

ERR_MSG_CANT_PARSE_ENTITY = ("Can't parse entities: can't find end of {entity_type}"
                             " entity at byte offset {offset}")

ERR_MSG_EMPTY_STR = "Message text is empty"
ERR_TEXT_MUST_BE_NON_EMPTY = "Text must be non-empty"

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

    @pytest.mark.parametrize("e_char, e_type", (
            ("*", MessageEntityType.BOLD),
            ("_", MessageEntityType.ITALIC),
            ("__", MessageEntityType.UNDERLINE),
            ("~", MessageEntityType.STRIKETHROUGH),
            ("||", MessageEntityType.SPOILER),
            ("`", MessageEntityType.CODE),
    ))
    def test_unescaped_entity_characters(self, e_char, e_type):
        template = "A string with an unescaped {0} character"
        with pytest.raises(BadMarkupException,
                           match=re.escape(ERR_MSG_CANT_PARSE_ENTITY.format(entity_type=e_type,
                                                                            offset=27))):
            self.ep.parse_markdown_v2(template.format(e_char))

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


class TestSimpleEntities:
    ep = EntityParser()

    @pytest.mark.parametrize("e_char, e_type", (
            ("*", MessageEntityType.BOLD),
            ("_", MessageEntityType.ITALIC),
            ("__", MessageEntityType.UNDERLINE),
            ("~", MessageEntityType.STRIKETHROUGH),
            ("||", MessageEntityType.SPOILER),
            ("`", MessageEntityType.CODE),
    ))
    def test_one_line_text_with_entity(self, e_char, e_type):
        template = "A single line string {0}with an entity{0}"
        resp = self.ep.parse_markdown_v2(template.format(e_char))
        assert resp == ("A single line string with an entity",
                            (MessageEntity(length=14, offset=21, type=e_type),))

    @pytest.mark.parametrize("e_char, e_type", (
            ("*", MessageEntityType.BOLD),
            ("_", MessageEntityType.ITALIC),
            ("__", MessageEntityType.UNDERLINE),
            ("~", MessageEntityType.STRIKETHROUGH),
            ("||", MessageEntityType.SPOILER),
            ("`", MessageEntityType.CODE),
    ))
    def test_multi_line_text_with_entity(self, e_char, e_type):
        template = "A multi line string {0}with\n an entity{0}"
        resp = self.ep.parse_markdown_v2(template.format(e_char))
        assert resp == ("A multi line string with\n an entity",
                            (MessageEntity(length=15, offset=20, type=e_type),))

    @pytest.mark.parametrize("e_char, e_type", (
            ("*", MessageEntityType.BOLD),
            ("_", MessageEntityType.ITALIC),
            ("__", MessageEntityType.UNDERLINE),
            ("~", MessageEntityType.STRIKETHROUGH),
            ("||", MessageEntityType.SPOILER),
            ("`", MessageEntityType.CODE),
    ))
    @pytest.mark.parametrize(["escaped_char"], RESERVED_ENTITY_CHARS + RESERVED_REGULAR_CHARS)
    def test_entity_with_escaped_char_in_it(self, e_char, e_type, escaped_char):
        template = (f"A multiline string with {e_char}entity\n"
                    rf"and escaped char \{escaped_char} within{e_char} the entity")

        resp = self.ep.parse_markdown_v2(template)
        assert resp == (f"A multiline string with entity\n"
                            f"and escaped char {escaped_char} within the entity",
                        (MessageEntity(length=32, offset=24, type=e_type),))

    @pytest.mark.parametrize("e_char, e_type", (
            ("*", MessageEntityType.BOLD),
            ("_", MessageEntityType.ITALIC),
            ("__", MessageEntityType.UNDERLINE),
            ("~", MessageEntityType.STRIKETHROUGH),
            ("||", MessageEntityType.SPOILER),
            ("`", MessageEntityType.CODE),
    ))
    def test_with_leading_and_trailing_whitespace_inside_entity_in_different_parts_of_the_message(self, e_char, e_type):
        text = f"{e_char}hello\n\n\n\nworld\n\n\n\n\n{e_char}    {e_char}and one\nmore   \n\n\nline\n\n   {e_char}"
        resp = self.ep.parse_markdown_v2(text)

        assert resp ==  ('hello\n\n\n\nworld\n\n\n\n\n    and one\nmore   \n\n\nline',
                            (MessageEntity(length=19, offset=0, type=e_type),
                             MessageEntity(length=22, offset=23, type=e_type)))

    @pytest.mark.parametrize("e_char, e_type", (
            ("*", MessageEntityType.BOLD),
            ("_", MessageEntityType.ITALIC),
            ("__", MessageEntityType.UNDERLINE),
            ("~", MessageEntityType.STRIKETHROUGH),
            ("||", MessageEntityType.SPOILER),
            ("`", MessageEntityType.CODE),
    ))
    @pytest.mark.parametrize(["whitespace"], " \n")
    def test_with_leading_and_trailing_whitespaces_outside_entities(self, e_char, e_type, whitespace):
        text = f"{whitespace*4}New lines outside an {e_char} entity {e_char}\.{whitespace*4}"
        resp = self.ep.parse_markdown_v2(text)
        assert resp == ('New lines outside an  entity .',
                        (MessageEntity(length=8, offset=21, type=e_type),))

    @pytest.mark.parametrize("e_char, e_type", (
            ("*", MessageEntityType.BOLD),
            ("_", MessageEntityType.ITALIC),
            ("__", MessageEntityType.UNDERLINE),
            ("~", MessageEntityType.STRIKETHROUGH),
            ("||", MessageEntityType.SPOILER),
            ("`", MessageEntityType.CODE),
    ))
    @pytest.mark.parametrize(["whitespace"], " \n")
    def test_with_leading_and_trailing_whitespaces_inside_entities(self, e_char, e_type, whitespace):
        text = f"{e_char}{whitespace*3}Whitespaces{whitespace*5}{e_char} inside {e_char}{whitespace*2}entities{whitespace}{e_char}"
        resp = self.ep.parse_markdown_v2(text)
        assert resp ==  (f'{whitespace*3}Whitespaces{whitespace*5} inside {whitespace*2}entities',
                         (MessageEntity(length=19, offset=0, type=e_type),
                          MessageEntity(length=10, offset=27, type=e_type)))

