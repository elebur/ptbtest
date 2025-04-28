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
    """
    Simple entities are the entities that consist of the tag name only,
    and they don't need attributes.
    Some of the tags can be used both with and without attributes
    (e.g., `code`, `blockquote`), in this class only cases without
    attributes are tested.
    """
    ep = EntityParser()

    @pytest.mark.parametrize("tag_name, e_type", (("i", MessageEntityType.ITALIC),
                                                  ("em", MessageEntityType.ITALIC),
                                                  ("b", MessageEntityType.BOLD),
                                                  ("strong", MessageEntityType.BOLD),
                                                  ("s", MessageEntityType.STRIKETHROUGH),
                                                  ("strike", MessageEntityType.STRIKETHROUGH),
                                                  ("del", MessageEntityType.STRIKETHROUGH),
                                                  ("u", MessageEntityType.UNDERLINE),
                                                  ("ins", MessageEntityType.UNDERLINE),
                                                  ("tg-spoiler", MessageEntityType.SPOILER),
                                                  ("pre", MessageEntityType.PRE),
                                                  ("code", MessageEntityType.CODE),
                                                  ("blockquote", MessageEntityType.BLOCKQUOTE),))
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
                                                  ("ins", MessageEntityType.UNDERLINE),
                                                  ("tg-spoiler", MessageEntityType.SPOILER),
                                                  ("pre", MessageEntityType.PRE),
                                                  ("code", MessageEntityType.CODE),
                                                  ("blockquote", MessageEntityType.BLOCKQUOTE),
                                                  ))
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
                                                  ("ins", MessageEntityType.UNDERLINE),
                                                  ("tg-spoiler", MessageEntityType.SPOILER),
                                                  ("pre", MessageEntityType.PRE),
                                                  ("code", MessageEntityType.CODE),
                                                  ("blockquote", MessageEntityType.BLOCKQUOTE),
                                                  ))
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
                                                  ("ins", MessageEntityType.UNDERLINE),
                                                  ("tg-spoiler", MessageEntityType.SPOILER),
                                                  ("pre", MessageEntityType.PRE),
                                                  ("code", MessageEntityType.CODE),
                                                  ("blockquote", MessageEntityType.BLOCKQUOTE),
                                                  ))
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
                                                  ("ins", MessageEntityType.UNDERLINE),
                                                  ("tg-spoiler", MessageEntityType.SPOILER),
                                                  ("pre", MessageEntityType.PRE),
                                                  ("code", MessageEntityType.CODE),
                                                  ("blockquote", MessageEntityType.BLOCKQUOTE),
                                                  ))
    @pytest.mark.parametrize(["whitespace"], " \n")
    def test_with_leading_and_trailing_whitespaces_inside_entities(self, tag_name, e_type, whitespace):
        text = (f"<{tag_name}>{whitespace * 3}Whitespaces{whitespace * 5}</{tag_name}> "
                f"inside <{tag_name}>{whitespace * 2}entities{whitespace}</{tag_name}>")
        resp = self.ep.parse_html(text)
        assert resp ==  (f'{whitespace*3}Whitespaces{whitespace*5} inside {whitespace*2}entities',
                         (MessageEntity(length=19, offset=0, type=e_type),
                          MessageEntity(length=10, offset=27, type=e_type)))

    @pytest.mark.parametrize("tag_name, e_type", (("i", MessageEntityType.ITALIC),
                                                  ("em", MessageEntityType.ITALIC),
                                                  ("b", MessageEntityType.BOLD),
                                                  ("strong", MessageEntityType.BOLD),
                                                  ("s", MessageEntityType.STRIKETHROUGH),
                                                  ("strike", MessageEntityType.STRIKETHROUGH),
                                                  ("del", MessageEntityType.STRIKETHROUGH),
                                                  ("u", MessageEntityType.UNDERLINE),
                                                  ("ins", MessageEntityType.UNDERLINE),
                                                  ("tg-spoiler", MessageEntityType.SPOILER),
                                                  ("pre", MessageEntityType.PRE),
                                                  ("code", MessageEntityType.CODE),
                                                  ("blockquote", MessageEntityType.BLOCKQUOTE),
                                                  ))
    def test_embedded_unclosed_entity_failing(self, tag_name, e_type):
        template = "A single line string <{0}>with <a> an entity</{0}>"

        offset = 41 + len(tag_name)
        err_msg = (f"Can't parse entities: unmatched end tag at byte offset {offset}, "
                   f"expected \"</a>\", found \"</{tag_name}>\"")

        with pytest.raises(BadMarkupException, match=err_msg):
            self.ep.parse_html(template.format(tag_name))


class TestTagA:
    ep = EntityParser()

    def test_without_href(self):
        resp = self.ep.parse_html("<a>http://www.example.com/</a>")

        entity = resp[1][0]
        assert resp == ("http://www.example.com/", (MessageEntity(length=23,
                                                                  offset=0,
                                                                  type=MessageEntityType.TEXT_LINK,
                                                                  url='http://www.example.com/'),))
        assert entity.url == "http://www.example.com/"

    def test_href_attr_double_quotes(self):
        resp = self.ep.parse_html("<a href=\"http://www.example.com/\">inline URL</a>")

        entity = resp[1][0]
        assert resp == ('inline URL', (MessageEntity(length=10,
                                                     offset=0,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url='http://www.example.com/'),))
        assert entity.url == "http://www.example.com/"

    def test_href_attr_single_quotes(self):
        resp = self.ep.parse_html("<a href='http://www.example.com/'>inline URL</a>")

        entity = resp[1][0]
        assert resp == ('inline URL', (MessageEntity(length=10,
                                                     offset=0,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url='http://www.example.com/'),))
        assert entity.url == "http://www.example.com/"

    def test_empty_href(self):
        text = "<a href=''>hello</a>"

        resp = self.ep.parse_html(text)

        assert resp == ("hello", ())

    def test_empty_href_without_quotes_but_with_equal_sign(self):
        text = "<a href=>hello</a>"

        resp = self.ep.parse_html(text)

        assert resp == ("hello", ())

    def test_at_the_beginning(self):
        resp = self.ep.parse_html("<a href='example.com/'>hello</a> world")
        entity = resp[1][0]

        assert resp ==  ('hello world', (MessageEntity(length=5,
                                                       offset=0,
                                                       type=MessageEntityType.TEXT_LINK,
                                                       url='http://example.com/'),))
        assert entity.url == "http://example.com/"

    def test_at_the_end(self):
        resp = self.ep.parse_html("Say <a href='example.com/'>'hello'</a>")
        entity = resp[1][0]

        assert entity.url == "http://example.com/"
        assert resp ==  ("Say 'hello'", (MessageEntity(length=7,
                                                     offset=4,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url='http://example.com/'),))

    def test_in_the_middle(self):
        resp = self.ep.parse_html("URL <a href=\"https://example.com/login\">in the middle</a> of the message")

        entity = resp[1][0]

        assert entity.url == "https://example.com/login"
        assert resp == ('URL in the middle of the message', (MessageEntity(length=13,
                                                                           offset=4,
                                                                           type=MessageEntityType.TEXT_LINK,
                                                                           url='https://example.com/login'),))

    def test_multiple_inline_urls(self):
        resp = self.ep.parse_html("Multiple <a href='example.com/?param1=val1'>inline urls</a> "
                                         "within <a href='https://example.com'>one message</a>")

        entity1 = resp[1][0]
        entity2 = resp[1][1]

        assert entity1.url == "http://example.com/?param1=val1"
        assert entity2.url == "https://example.com/"

        assert resp == ('Multiple inline urls within one message',
                            (MessageEntity(length=11,
                                           offset=9,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://example.com/?param1=val1'),
                             MessageEntity(length=11,
                                           offset=28,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://example.com/')))

    def test_multiline_multiple_inline_urls_parts(self):
        resp = self.ep.parse_html('Multiple <a href="example.com/?param1=val1">inline urls</a>\n'
                                         'in <a href="http://example.com/">one message</a>.\n'
                                         'Each one on new line')
        entity1 = resp[1][0]
        entity2 = resp[1][1]

        assert entity1.url == "http://example.com/?param1=val1"
        assert entity2.url == "http://example.com/"

        assert resp == ('Multiple inline urls\nin one message.\nEach one on new line',
                            (MessageEntity(length=11,
                                           offset=9,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://example.com/?param1=val1'),
                             MessageEntity(length=11,
                                           offset=24,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://example.com/')))

    def test_named_html_entities_within_entity(self):
        resp = self.ep.parse_html("<a href='http://example.com/'>1 &lt; 2; 5 &gt; 3; "
                                  "1 == 1 &amp;&amp; &quot;a&quot; == &quot;a&quot; </a>")

        entity = resp[1][0]
        assert resp == ('1 < 2; 5 > 3; 1 == 1 && "a" == "a"',
                        (MessageEntity(length=34, offset=0,
                                       type=MessageEntityType.TEXT_LINK,
                                       url='http://example.com/'),))
        assert entity.url == "http://example.com/"

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_outside_of_entity(self, symbol):
        resp = self.ep.parse_html(f"{symbol*8}<a href='http://www.example.com'>inline URL</a>{symbol*33}")

        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"
        assert resp ==  ('inline URL', (MessageEntity(length=10,
                                                      offset=0,
                                                      type=MessageEntityType.TEXT_LINK,
                                                      url='http://www.example.com/'),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_entity(self, symbol):
        resp = self.ep.parse_html(f"<a href='http://www.example.com'>{symbol*2}inline URL{symbol*14}</a>")
        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"

        assert resp == (f'{symbol*2}inline URL', (MessageEntity(length=12,
                                                                offset=0,
                                                                type=MessageEntityType.TEXT_LINK,
                                                                url='http://www.example.com/'),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_entity_with_text_afterwards(self, symbol):
        resp = self.ep.parse_html(f"<a href='http://www.example.com'>{symbol * 2}"
                                  f"inline URL{symbol * 14}</a> some text")
        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"

        assert resp == (f'{symbol*2}inline URL{symbol*14} some text',
                            (MessageEntity(length=26,
                                           offset=0,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://www.example.com/'),))

    def test_trailing_whitespace_inside_entity_with_text_after_entity(self):
        text = (r"A string with trailing whitespace "
                r"<a href='http://www.example.com'>inside brackets </a>"
                r"and some text after.")
        resp = self.ep.parse_html(text)

        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"
        assert resp == ('A string with trailing whitespace inside brackets and some text after.',
                        (MessageEntity(length=16, offset=34,
                                       type=MessageEntityType.TEXT_LINK,
                                       url='http://www.example.com/'),))

    @pytest.mark.parametrize(
        "in_str, result", (("An  <a href='  http://www.example.com  '>inline URL</a>   ", ('An  inline URL', ())),
                           ("An  <a href='  http://www.example.com  '>inline URL</a>   Some text", ('An  inline URL   Some text', ())),
                           ("An  <a href='http://www.example.com  '>inline URL</a>   Some text", ('An  inline URL   Some text', ())),
                           ("An  <a href='  http://www.example.com'>inline URL</a>   Some text", ('An  inline URL   Some text', ())),
                           ("An  <a href='  http://www.example.com  '>inline URL</a>", ('An  inline URL', ())),
                           ("An  <a href='  http://www.example.com'>inline URL</a>", ('An  inline URL', ())),
                           ("An  <a href='http://www.example.com  '>inline URL</a>   ", ('An  inline URL', ())),
                           ("An  <a href='http://www.example.com  '>inline URL</a>", ('An  inline URL', ())),))
    def test_with_whitespaces_inside_attribute(self, in_str, result):
        resp = self.ep.parse_html(in_str)
        assert resp == result

    def test_with_newline_inside_href(self):
        resp = self.ep.parse_html("An  <a href='http://www.\nexample.com'>inline URL</a>")

        assert resp == ("An  inline URL", ())

    def test_newline_inside_entity(self):
        resp = self.ep.parse_html("Test new line <a href=\"http://www.example.com/\">inside \n inline URL</a> text")
        assert resp == ('Test new line inside \n inline URL text',
                            (MessageEntity(length=19,
                                           offset=14,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://www.example.com/'),))

    def test_empty_entity_failing(self):
        with pytest.raises(BadMarkupException, match=re.escape(ERR_TEXT_MUST_BE_NON_EMPTY)):
            self.ep.parse_html("<a></a>")

    def test_empty_text_part_failing(self):
        with pytest.raises(BadMarkupException, match=re.escape(ERR_TEXT_MUST_BE_NON_EMPTY)):
            self.ep.parse_html("<a href='example.com'></a>")

    def test_empty_url_part(self):
        resp = self.ep.parse_html("<a>empty url</a>")
        assert resp == ('empty url', ())

    def test_nested_simple_entities(self):
        text = ("A string with <a href='https://example.com'>"
                "<b>a</b> <i>nested</i> <s>enn</s><u>ti</u>"
                "<tg-spoiler>ty</tg-spoiler>"
                "</a>")

        resp = self.ep.parse_html(text)

        assert resp == ('A string with a nested enntity',(MessageEntity(length=16,
                                                                        offset=14,
                                                                        type=MessageEntityType.TEXT_LINK,
                                                                        url='http://outer.com/'),
                                                          MessageEntity(length=1,
                                                                        offset=14,
                                                                        type=MessageEntityType.BOLD),
                                                          MessageEntity(length=6,
                                                                        offset=16,
                                                                        type=MessageEntityType.ITALIC),
                                                          MessageEntity(length=3,
                                                                        offset=23,
                                                                        type=MessageEntityType.STRIKETHROUGH),
                                                          MessageEntity(length=2,
                                                                        offset=26,
                                                                        type=MessageEntityType.UNDERLINE),
                                                          MessageEntity(length=2,
                                                                        offset=28,
                                                                        type=MessageEntityType.SPOILER)))

    def test_with_emoji(self):
        text = "👨‍👩‍👧‍👦 😊😊 <a href='ex.com'>A string with emojis 😊</a> 😊😊"
        resp = self.ep.parse_html(text)
        assert resp == ("👨‍👩‍👧‍👦 😊😊 A string with emojis 😊 😊😊",
                            (MessageEntity(length=23,
                                           offset=17,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://ex.com/'),))

    def test_non_latin_characters(self):
        resp = self.ep.parse_html("<a href='ex.com'>你好世界!</a>")
        assert resp == ('你好世界!', (MessageEntity(length=5,
                                                    offset=0,
                                                    type=MessageEntityType.TEXT_LINK,
                                                    url='http://ex.com/'),))


class TestMention:
    """
    As for April 2025, inline mentioning doesn't work (from the server side).
    """
    def test_mention(self):
        text = '<a href="tg://user?id=123456789">inline mention of a user</a>'
        resp = EntityParser.parse_html(text)

        assert resp == ("inline mention of a user", ())


class TestTagSpan:
    ep = EntityParser()

    def test_with_attribute(self):
        text = '<span class="tg-spoiler">spoiler</span>'

        resp = self.ep.parse_html(text)

        assert resp == ('spoiler', (MessageEntity(length=7, offset=0,
                                                  type=MessageEntityType.SPOILER),))

    def test_with_wrong_attribute_failing(self):
        text = '<span class="spoiler">spoiler</span>'
        err_msg = 'Can\'t parse entities: tag "span" must have class "tg-spoiler" at byte offset 0'
        with pytest.raises(BadMarkupException, match=err_msg):
            self.ep.parse_html(text)

    def test_without_attribute_failing(self):
        text = '<span>spoiler</span>'
        err_msg = 'Can\'t parse entities: tag "span" must have class "tg-spoiler" at byte offset 0'
        with pytest.raises(BadMarkupException, match=err_msg):
            self.ep.parse_html(text)


class TestPreAndCode:
    ep = EntityParser()

    def test_code_nested_into_pre_with_language(self):
        text = ('<pre><code class="language-python">pre-formatted '
                'fixed-width code block written </code></pre>')

        resp = self.ep.parse_html(text)
        entity = resp[1][0]
        assert entity.language == 'python'
        assert resp == ('pre-formatted fixed-width code block written',
                        (MessageEntity(length=44, offset=0, language='python',
                                       type=MessageEntityType.PRE),))

    def test_code_nested_into_pre_without_language(self):
        text = ('<pre><code>pre-formatted '
                'fixed-width code block written </code></pre>')

        resp = self.ep.parse_html(text)

        entity = resp[1][0]
        # There is only one entity.
        assert len(resp[1]) == 1
        assert entity.language is None
        assert resp == ('pre-formatted fixed-width code block written',
                        (MessageEntity(length=44, offset=0, type=MessageEntityType.PRE),))

    def test_code_nested_into_pre_with_wrong_attribute(self):
        text = ('<pre><code class="spoiler">pre-formatted '
                'fixed-width code block written </code></pre>')

        resp = self.ep.parse_html(text)

        entity = resp[1][0]
        # There is only one entity.
        assert len(resp[1]) == 1
        assert entity.language is None
        assert resp == ('pre-formatted fixed-width code block written',
                        (MessageEntity(length=44, offset=0, type=MessageEntityType.PRE),))

    def test_pre_nested_into_code_with_language(self):
        text = ('<code><pre class="language-python">pre-formatted '
                'fixed-width code block written </pre></code>')

        resp = self.ep.parse_html(text)

        entity = resp[1][0]
        # There is only one entity.
        assert len(resp[1]) == 1
        assert entity.language is None
        assert resp == ('pre-formatted fixed-width code block written',
                        (MessageEntity(length=44, offset=0, type=MessageEntityType.PRE),))

    def test_pre_nested_into_code_without_language(self):
        text = ('<code><pre>pre-formatted '
                'fixed-width code block written </pre></code>')

        resp = self.ep.parse_html(text)

        entity = resp[1][0]
        # There is only one entity.
        assert len(resp[1]) == 1
        assert entity.language is None
        assert resp == ('pre-formatted fixed-width code block written',
                        (MessageEntity(length=44, offset=0, type=MessageEntityType.PRE),))

    def test_standalone_pre_with_language(self):
        text = ('<pre class="language-python">pre-formatted '
                'fixed-width code block written </pre>')

        resp = self.ep.parse_html(text)

        entity = resp[1][0]
        assert entity.language is None
        assert resp == ('pre-formatted fixed-width code block written',
                        (MessageEntity(length=44, offset=0, type=MessageEntityType.PRE),))

    def test_standalone_code_with_language(self):
        text = ('<code class="language-python">pre-formatted '
                'fixed-width code block written </code>')

        resp = self.ep.parse_html(text)

        entity = resp[1][0]
        assert entity.language is None
        assert resp == ('pre-formatted fixed-width code block written',
                        (MessageEntity(length=44, offset=0, type=MessageEntityType.CODE),))
