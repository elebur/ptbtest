import re

import pytest
from telegram import MessageEntity
from telegram.constants import MessageEntityType

from ptbtest.entityparser import EntityParser, _decode_html_entity
from ptbtest.errors import BadMarkupException

ERR_MSG_EMPTY_STR = "Message text is empty"
ERR_TEXT_MUST_BE_NON_EMPTY = "Text must be non-empty"


class TestDecodeHtmlEntity:

    def test_empty_string(self):
        assert _decode_html_entity("", 0) == (None, 0)

    def test_invalid_position(self):
        # The exact length of the string.
        assert _decode_html_entity("&#65;", 5) == (None, 5)
        # Greater than the length of the string.
        assert _decode_html_entity("&#65;", 10) == (None, 10)
        # The negative position.
        assert _decode_html_entity("&#65;", -10) == (None, -10)

    def test_hex_overflow(self):
        # Max valid code point
        assert _decode_html_entity("&#x10FFFE;", 0) == ("\\U0010fffe", 10)
        # Invalid (out of Unicode range)
        assert _decode_html_entity("&#x10FFFF;", 0) == (None, 0)
        assert _decode_html_entity("&#x110000;", 0) == (None, 0)

    def test_decimal_overflow(self):
        # Max valid code point
        assert _decode_html_entity("&#1114110;", 0) == ("\\U0010fffe", 10)
        # Invalid (out of Unicode range)
        assert _decode_html_entity("&#1114111;", 0) == (None, 0)
        assert _decode_html_entity("&#1114112;", 0) == (None, 0)

    @pytest.mark.parametrize(["text"], (("&", ), ("& ", ), ("&!", ), ("&@", )))
    def test_ampersand_not_followed_by_entity(self, text):
        assert _decode_html_entity(text, 0) == (None, 0)

    @pytest.mark.parametrize(["entity"], (("&#",), ("&",), ("&#x",)))
    def test_incomplete_entity(self, entity):
        assert _decode_html_entity(entity, 0) == (None, 0)

    @pytest.mark.parametrize("raw, entity, end_pos", (
            ("lt", "<", 18),
            ("gt", ">", 18),
            ("amp", "&", 19),
            ("quot", "\"", 20),))
    def test_valid_named_entities_with_semicolon_at_the_end(self, raw, entity, end_pos):
        text = f"A string with &{raw}; entity in it."

        result = _decode_html_entity(text, 14)

        assert result == (entity, end_pos)

    @pytest.mark.parametrize("raw, entity, end_pos", (
            ("lt", "<", 17),
            ("gt", ">", 17),
            ("amp", "&", 18),
            ("quot", "\"", 19),))
    def test_valid_named_entities_without_semicolon_at_the_end(self, raw, entity, end_pos):
        text = f"A string with &{raw} entity in it."

        result = _decode_html_entity(text, 14)

        assert result == (entity, end_pos)

    @pytest.mark.parametrize(["entity_code"], (("euro", ), ("reg", ), ("copy", ), ("trade", ), ))
    def test_invalid_named_entities(self, entity_code):
        text = f"A string with &{entity_code}; entity in it."

        result = _decode_html_entity(text, 14)

        assert result == (None, 14)

    @pytest.mark.parametrize(["entity"], (("&LT;", ), ("&GT;", ), ("&AMP;", ), ("&QUOT;", ),))
    def test_upper_case_valid_named_entities(self, entity):
        assert _decode_html_entity(entity, 0) == (None, 0)

    @pytest.mark.parametrize(["entity"], (("&Lt;", ), ("&gT;", ), ("&amP;", ), ("&QUot;", ),))
    def test_mixed_case_named_entities(self, entity):
        assert _decode_html_entity(entity, 0) == (None, 0)

    def test_non_ampersand_char_at_start_position(self):
        text = "A string with wrong &lt; start position."
        err_msg = "The character ('w') at the position 9 is not '&'"
        with pytest.raises(ValueError, match=re.escape(err_msg)):
            _decode_html_entity(text, 9)

    @pytest.mark.parametrize("entity, code, end_pos", (("&#65;", "A", 5),
                                                       ("&#97;", "a", 5),
                                                       ("&#165;", "¥", 6),
                                                       # No semicolon
                                                       ("&#8869", "⊥", 6),
                                                       ("&#9827", "♣", 6),
                                                       ("&#338", "Œ", 5),))
    def test_valid_decimal_numeric_entity(self, entity, code, end_pos):
        result = _decode_html_entity(entity, 0)

        assert result == (code, end_pos)

    @pytest.mark.parametrize(["entity"], (("&#0;", ),
                                          ("&#1234567891011;", ),
                                          ("&#-165;", ),
                                          ("&#AAA", ),
                                          ("&#9999999;", ),))
    def test_invalid_decimal_numeric_entity(self, entity):
        result = _decode_html_entity(entity, 0)

        assert result == (None, 0)

    def test_partially_valid_decimal_entity(self):
        # '&#62' is a valid HTML decimal entity, while "AA" is an invalid part.
        assert _decode_html_entity("&#62AA", 0) == (">", 4)

    @pytest.mark.parametrize("entity, code, end_pos", (("&#x41;", "A", 6),
                                                       ("&#x7A;", "z", 6),
                                                       ("&#x174;", "Ŵ", 7),
                                                       # No semicolon
                                                       ("&#x20AC", "€", 7),
                                                       ("&#xbc", "¼", 5),
                                                       ("&#x0234", "ȴ", 7),))
    def test_valid_hex_entity(self, entity, code, end_pos):
        result = _decode_html_entity(entity, 0)

        assert result == (code, end_pos)

    @pytest.mark.parametrize(["entity"], (("&#x0;", ),
                                          ("&#xRTX", ),
                                          ("&#xRTX;", ),))
    def test_invalid_hex_numeric_entity(self, entity):
        result = _decode_html_entity(entity, 0)

        assert result == (None, 0)

    @pytest.mark.parametrize("lower_case, upper_case, code, end_pos", (
            ("&#xaaa;", "&#XAAA;", "પ", 7),
            ("&#xaab;", "&#XAAB;", "ફ", 7),
            ("&#Xaac;", "&#xAAC;", "બ", 7),))
    def test_upper_and_lower_cases(self, lower_case, upper_case, code, end_pos):
        assert _decode_html_entity(lower_case, 0) == _decode_html_entity(upper_case, 0) == (code, end_pos)

    def test_partially_valid_hex_entity(self):
        # '&#xAAA' is a valid HTML hex entity, while "RTX" is an invalid part.
        assert _decode_html_entity("&#xAAARTX", 0) == ("પ", 6)

    def test_multiple_entities_in_a_row(self):
        """
        Must receive only the first entity.
        """
        text = "&lt;&gt;&amp;"
        result = _decode_html_entity(text, 0)
        assert result == ("<", 4)

    def test_without_semicolon(self):
        assert _decode_html_entity("&#65", 0) == ("A", 4)
        assert _decode_html_entity("&amp", 0) == ("&", 4)

    def test_valid_named_entity_embedded_in_word(self):
        assert _decode_html_entity("&ltxyz", 0) == (None, 0)
        assert _decode_html_entity("&ampersand", 0) == (None, 0)

    def test_numeric_entities_with_non_ascii_digits(self):
        """
        This test is here to make sure that string.isdigit()/isnumeric()/isdecimal()
        weren't used in _decode_html_entity.
        """
        # https://stackoverflow.com/a/54912545/19813684

        # ARABIC-INDIC DIGIT ZERO~NINE
        assert _decode_html_entity("&#٢٣;", 0) == (None, 0)
        # SUPERSCRIPT ZERO~NINE
        assert _decode_html_entity("&#³⁴;", 0) == (None, 0)
        # ROMAN NUMERAL
        assert _decode_html_entity("&#ⅤⅥ;", 0) == (None, 0)


class TestNoEntities:
    ep = EntityParser()
    def test_empty_string(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_EMPTY_STR):
            self.ep.parse_html("")

    def test_single_line_text(self):
        resp = self.ep.parse_html("A single line text")
        assert resp == ("A single line text", ())

    def test_multiline_string(self):
        resp = self.ep.parse_html("A string\non three\nlines")
        assert resp == ("A string\non three\nlines", ())

    def test_multiline_string_with_leading_and_trailing_whitespaces(self):
        resp = self.ep.parse_html("   A multiline\nstring\nwith leading and\ntrailing \nwhitespaces     ")
        assert resp == ("A multiline\nstring\nwith leading and\ntrailing \nwhitespaces", ())

    def test_multiline_string_with_leading_and_trailing_newlines(self):
        resp = self.ep.parse_html("\n\n \nA multiline\nstring\nwith leading and\ntrailing \nnewlines \n  \n")
        assert resp == ("A multiline\nstring\nwith leading and\ntrailing \nnewlines", ())


class TestSimpleEntities:
    ep = EntityParser()

    @pytest.mark.parametrize("tag_name, e_type", (("i", MessageEntityType.ITALIC),
                                                  ("em", MessageEntityType.ITALIC),
                                                  ("b", MessageEntityType.BOLD),
                                                  ("strong", MessageEntityType.BOLD),
                                                  ("s", MessageEntityType.STRIKETHROUGH),
                                                  ("strike", MessageEntityType.STRIKETHROUGH),
                                                  ("del", MessageEntityType.STRIKETHROUGH),
                                                  ("u", MessageEntityType.UNDERLINE),
                                                  ("ins", MessageEntityType.UNDERLINE),))
    def test_one_line_text_with_entity(self, tag_name, e_type):
        template = "A single line string <{0}>with an entity</{0}>"
        resp = self.ep.parse_html(template.format(tag_name))
        assert resp == ("A single line string with an entity",
                            (MessageEntity(length=14, offset=21, type=e_type),))

    @pytest.mark.parametrize("tag_name, e_type", (("i", MessageEntityType.ITALIC),
                                                  ("em", MessageEntityType.ITALIC),
                                                  ("b", MessageEntityType.BOLD),
                                                  ("strong", MessageEntityType.BOLD),
                                                  ("s", MessageEntityType.STRIKETHROUGH),
                                                  ("strike", MessageEntityType.STRIKETHROUGH),
                                                  ("del", MessageEntityType.STRIKETHROUGH),
                                                  ("u", MessageEntityType.UNDERLINE),
                                                  ("ins", MessageEntityType.UNDERLINE),))
    def test_multi_line_text_with_entity(self, tag_name, e_type):
        template = "A multi line string <{0}>with\n an entity</{0}>"
        resp = self.ep.parse_html(template.format(tag_name))
        assert resp == ("A multi line string with\n an entity",
                            (MessageEntity(length=15, offset=20, type=e_type),))

    @pytest.mark.parametrize("tag_name, e_type", (("i", MessageEntityType.ITALIC),
                                                  ("em", MessageEntityType.ITALIC),
                                                  ("b", MessageEntityType.BOLD),
                                                  ("strong", MessageEntityType.BOLD),
                                                  ("s", MessageEntityType.STRIKETHROUGH),
                                                  ("strike", MessageEntityType.STRIKETHROUGH),
                                                  ("del", MessageEntityType.STRIKETHROUGH),
                                                  ("u", MessageEntityType.UNDERLINE),
                                                  ("ins", MessageEntityType.UNDERLINE),))
    def test_with_leading_and_trailing_whitespace_inside_entity_in_different_parts_of_the_message(self, tag_name, e_type):
        text = (f"<{tag_name}>hello\n\n\n\nworld\n\n\n\n\n</{tag_name}>    "
                f"<{tag_name}>and one\nmore   \n\n\nline\n\n   </{tag_name}>")
        resp = self.ep.parse_html(text)

        assert resp ==  ('hello\n\n\n\nworld\n\n\n\n\n    and one\nmore   \n\n\nline',
                            (MessageEntity(length=19, offset=0, type=e_type),
                             MessageEntity(length=22, offset=23, type=e_type)))

    @pytest.mark.parametrize("tag_name, e_type", (("i", MessageEntityType.ITALIC),
                                                  ("em", MessageEntityType.ITALIC),
                                                  ("b", MessageEntityType.BOLD),
                                                  ("strong", MessageEntityType.BOLD),
                                                  ("s", MessageEntityType.STRIKETHROUGH),
                                                  ("strike", MessageEntityType.STRIKETHROUGH),
                                                  ("del", MessageEntityType.STRIKETHROUGH),
                                                  ("u", MessageEntityType.UNDERLINE),
                                                  ("ins", MessageEntityType.UNDERLINE),))
    @pytest.mark.parametrize(["whitespace"], " \n")
    def test_with_leading_and_trailing_whitespaces_outside_entities(self, tag_name, e_type, whitespace):
        text = fr"{whitespace*4}New lines outside an <{tag_name}> entity </{tag_name}>\.{whitespace * 4}"
        resp = self.ep.parse_html(text)
        assert resp == ("New lines outside an  entity \.",
                        (MessageEntity(length=8, offset=21, type=e_type),))

    @pytest.mark.parametrize("tag_name, e_type", (("i", MessageEntityType.ITALIC),
                                                  ("em", MessageEntityType.ITALIC),
                                                  ("b", MessageEntityType.BOLD),
                                                  ("strong", MessageEntityType.BOLD),
                                                  ("s", MessageEntityType.STRIKETHROUGH),
                                                  ("strike", MessageEntityType.STRIKETHROUGH),
                                                  ("del", MessageEntityType.STRIKETHROUGH),
                                                  ("u", MessageEntityType.UNDERLINE),
                                                  ("ins", MessageEntityType.UNDERLINE),))
    @pytest.mark.parametrize(["whitespace"], " \n")
    def test_with_leading_and_trailing_whitespaces_inside_entities(self, tag_name, e_type, whitespace):
        text = (f"<{tag_name}>{whitespace * 3}Whitespaces{whitespace * 5}</{tag_name}> "
                f"inside <{tag_name}>{whitespace * 2}entities{whitespace}</{tag_name}>")
        resp = self.ep.parse_html(text)
        assert resp ==  (f'{whitespace*3}Whitespaces{whitespace*5} inside {whitespace*2}entities',
                         (MessageEntity(length=19, offset=0, type=e_type),
                          MessageEntity(length=10, offset=27, type=e_type)))
