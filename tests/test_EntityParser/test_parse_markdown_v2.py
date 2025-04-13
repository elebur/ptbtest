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


class TestInlineUrl:
    ep = EntityParser()

    def test_url_message_consists_of_one_entity_only(self):
        resp = self.ep.parse_markdown_v2("[inline URL](http://www.example.com/)")

        entity = resp[1][0]
        assert resp == ('inline URL', (MessageEntity(length=10,
                                                     offset=0,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url='http://www.example.com/'),))
        assert entity.url == "http://www.example.com/"

    def test_at_the_beginning(self):
        resp = self.ep.parse_markdown_v2("[hello](example.com/) world")
        entity = resp[1][0]

        assert resp ==  ('hello world', (MessageEntity(length=5,
                                                       offset=0,
                                                       type=MessageEntityType.TEXT_LINK,
                                                       url='http://example.com/'),))
        assert entity.url == "http://example.com/"

    def test_at_the_end(self):
        resp = self.ep.parse_markdown_v2("Say '[hello](example.com)'")
        entity = resp[1][0]

        assert entity.url == "http://example.com/"
        assert resp ==  ("Say 'hello'", (MessageEntity(length=5,
                                                     offset=5,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url='http://example.com/'),))

    def test_in_the_middle(self):
        resp = self.ep.parse_markdown_v2("URL [in the middle](https://example.com/login) of the message")
        entity = resp[1][0]

        assert entity.url == "https://example.com/login"

        assert resp == ('URL in the middle of the message', (MessageEntity(length=13,
                                                                           offset=4,
                                                                           type=MessageEntityType.TEXT_LINK,
                                                                           url='https://example.com/login'),))

    def test_multiple_inline_urls(self):
        resp = self.ep.parse_markdown_v2("Multiple [inline urls](example.com/?param1=val1) "
                                         "within [one message](http://example.com/)")

        entity1 = resp[1][0]
        entity2 = resp[1][1]

        assert entity1.url == "http://example.com/?param1=val1"
        assert entity2.url == "http://example.com/"

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
        resp = self.ep.parse_markdown_v2('Multiple [inline urls](example.com/?param1=val1)\n'
                                         'in [one message](http://example.com/)\.\n'
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

    def test_escaped_symbol(self):
        resp = self.ep.parse_markdown_v2("A message with an [inline url](example.com/)"
                                         "and escaped symbols \[\]\.")
        entity = resp[1][0]

        assert entity.url == "http://example.com/"

        assert resp ==  ('A message with an inline urland escaped symbols [].',
                            (MessageEntity(length=10,
                                           offset=18,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://example.com/'),))

    @pytest.mark.parametrize(["symbol", ], "[]()")
    def test_escaped_inline_url_symbols_inside_entity(self, symbol):
        text = rf"[inline \{symbol} url](https://example.com/)"

        resp = self.ep.parse_markdown_v2(text)
        entity = resp[1][0]

        assert entity.url == "https://example.com/"

        assert resp == (f'inline {symbol} url', (MessageEntity(length=12, offset=0, type=MessageEntityType.TEXT_LINK, url='https://example.com/'),))

    @pytest.mark.parametrize(["symbol", ], RESERVED_REGULAR_CHARS)
    def test_regular_unescaped_symbols_inside_inline_url(self, symbol):
        text = rf"A string with an [inline URL and unescaped '{symbol}'](http://www.example.com) in it\."
        with pytest.raises(BadMarkupException, match=re.escape(ERR_MSG_CHAR_MUST_BE_ESCAPED.format(f"{symbol}"))):
            print(text)
            self.ep.parse_markdown_v2(text)

    @pytest.mark.parametrize(["e_char"], (("*",),("_",),("__",),("~",),("||",),))
    def test_entity_unescaped_symbols_inside_inline_url(self, e_char):
        text = rf"A string with an [inline URL and unescaped '{e_char}'](http://www.example.com) in it\."
        with pytest.raises(BadMarkupException, match=re.escape(ERR_MSG_CHAR_MUST_BE_ESCAPED.format("]"))):
            self.ep.parse_markdown_v2(text)

    def test_unescaped_code_symbol_inside_inline_url(self):
        text = rf"A string with an [inline URL and unescaped '`'](http://www.example.com) in it\."
        with pytest.raises(BadMarkupException, match=ERR_MSG_CANT_PARSE_ENTITY.format(entity_type="code",
                                                                                      offset=44)):
            self.ep.parse_markdown_v2(text)

    def test_unclosed_square_brackets(self):
        with pytest.raises(BadMarkupException, match=re.escape(ERR_MSG_CHAR_MUST_BE_ESCAPED.format("("))):
            self.ep.parse_markdown_v2("Test [unclosed entity(http://example.com)")

    def test_unclosed_parentheses(self):
        err_msg = "Can't parse entities: can't find end of a url at byte offset 13"
        with pytest.raises(BadMarkupException, match=err_msg):
            self.ep.parse_markdown_v2("[inline URL](http://www.example.com")

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_outside_of_entity(self, symbol):
        resp = self.ep.parse_markdown_v2(f"{symbol*8}[inline URL](http://www.example.com){symbol*33}")
        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"

        assert resp == ('inline URL', (MessageEntity(length=10,
                                                     offset=0,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url='http://www.example.com/'),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_square_brackets(self, symbol):
        resp = self.ep.parse_markdown_v2(f"[{symbol*2}inline URL{symbol*14}](http://www.example.com)")
        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"

        assert resp == (f'{symbol*2}inline URL', (MessageEntity(length=12,
                                                                offset=0,
                                                                type=MessageEntityType.TEXT_LINK,
                                                                url='http://www.example.com/'),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_square_brackets_with_text_afterwards(self, symbol):
        resp = self.ep.parse_markdown_v2(f"[{symbol*2}inline URL{symbol*14}](http://www.example.com) some text")
        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"

        assert resp == (f'{symbol*2}inline URL{symbol*14} some text',
                            (MessageEntity(length=26,
                                           offset=0,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://www.example.com/'),))

    def test_trailing_whitespace_inside_square_brackets_with_text_after_entity(self):
        text = "A string with trailing whitespace [inside square brackets ](http://www.example.com)in it\."
        resp = self.ep.parse_markdown_v2(text)

        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"

        assert resp == (f"A string with trailing whitespace inside square brackets in it.",
                        (MessageEntity(length=23,
                                       offset=34,
                                       type=MessageEntityType.TEXT_LINK,
                                       url='http://www.example.com/'),))

    @pytest.mark.parametrize(
        "input, result", (("An  [inline URL](  http://www.example.com  )   ", ('An  inline URL', ())),
                          ("An  [inline URL](  http://www.example.com  )   Some text", ('An  inline URL   Some text', ())),
                          ("An  [inline URL](http://www.example.com  )   Some text", ('An  inline URL   Some text', ())),
                          ("An  [inline URL](  http://www.example.com)   Some text", ('An  inline URL   Some text', ())),
                          ("An  [inline URL](  http://www.example.com  )", ('An  inline URL', ())),
                          ("An  [inline URL](  http://www.example.com)", ('An  inline URL', ())),
                          ("An  [inline URL](http://www.example.com  )   ", ('An  inline URL', ())),
                          ("An  [inline URL](http://www.example.com  )", ('An  inline URL', ())),
                          ))
    def test_with_whitespaces_inside_parentheses(self, input, result):
        resp = self.ep.parse_markdown_v2(input)
        assert resp == result

    def test_with_space_between_square_brackets_and_parentheses(self):

        with pytest.raises(BadMarkupException, match=re.escape(ERR_MSG_CHAR_MUST_BE_ESCAPED.format("("))):
            self.ep.parse_markdown_v2("[inline URL] (http://www.example.com)")

    def test_with_newline_between_square_brackets_and_parentheses(self):
        with pytest.raises(BadMarkupException, match=re.escape(ERR_MSG_CHAR_MUST_BE_ESCAPED.format("("))):
            self.ep.parse_markdown_v2("[inline URL]\n(http://www.example.com)")

    @pytest.mark.xfail(reason="Need to implement parse_url_entities")
    def test_with_space_between_square_brackets_and_parentheses_and_text_afterwards(self):
        with pytest.raises(BadMarkupException, match=re.escape(ERR_MSG_CHAR_MUST_BE_ESCAPED.format("("))):
            self.ep.parse_markdown_v2("[inline URL] (http://www.example.com) some text here")

    @pytest.mark.parametrize(["url"], (("http://www.example.com/",),
                                       ("https://www.example.com/",),
                                       ("www.example.com/",),
                                       ("www.example.com",),
                                       ))
    def test_urls_without_path_and_params(self, url):
        resp = self.ep.parse_markdown_v2(f"[inline URL]({url})")
        protocol = "http"
        if url.startswith("https://"):
            protocol = "https"

        entity = resp[1][0]
        assert resp == ('inline URL', (MessageEntity(length=10,
                                                     offset=0,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url=f'{protocol}://www.example.com/'),))
        assert entity.url == f'{protocol}://www.example.com/'

    @pytest.mark.parametrize(["url", "path",],
                                (("www.example.com/", "login"),
                                ("www.example.com/", "login&param1=val1&param2=val2&param3"),
                                ("https://www.example.com/", "login"),
                                ("https://www.example.com/", "login&param1=val1&param2=val2&param3"),
                                ))
    def test_urls_with_path_and_params(self, url, path):
        resp = self.ep.parse_markdown_v2(f"[inline URL]({url}{path})")
        protocol = "http"
        if url.startswith("https://"):
            protocol = "https"

        entity = resp[1][0]
        assert resp == ('inline URL', (MessageEntity(length=10,
                                                     offset=0,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url=f'{protocol}://www.example.com/'),))
        assert entity.url == f'{protocol}://www.example.com/{path}'

    @pytest.mark.parametrize(["url"], (("http://example.com/",),
                                       ("https://example.com/",),
                                       ("example.com/",),
                                       ("example.com",),
                                       ))
    def test_urls_without_path_and_without_params_and_without_www(self, url):
        resp = self.ep.parse_markdown_v2(f"[inline URL]({url})")
        protocol = "http"
        if url.startswith("https://"):
            protocol = "https"

        entity = resp[1][0]
        assert resp == ('inline URL', (MessageEntity(length=10,
                                                     offset=0,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url=f'{protocol}://example.com/'),))
        assert entity.url == f'{protocol}://example.com/'

    @pytest.mark.parametrize(["url", "path",],
                                (("example.com/", "login"),
                                ("example.com/", "login&param1=val1&param2=val2&param3"),
                                ("https://example.com/", "login"),
                                ("https://example.com/", "login&param1=val1&param2=val2&param3"),
                                ))
    def test_urls_with_path_and_with_params_and_without_www(self, url, path):
        resp = self.ep.parse_markdown_v2(f"[inline URL]({url}{path})")
        protocol = "http"
        if url.startswith("https://"):
            protocol = "https"

        entity = resp[1][0]
        assert resp == ('inline URL', (MessageEntity(length=10,
                                                     offset=0,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url=f'{protocol}://example.com/'),))
        assert entity.url == f'{protocol}://example.com/{path}'

    def test_open_close_square_brackets_inside_square_brackets(self):
        resp = self.ep.parse_markdown_v2("[inline [] URL](http://www.example.com/)")

        assert resp == ("inline  URL",
                        (MessageEntity(length=11,
                                       offset=0,
                                       type=MessageEntityType.TEXT_LINK,
                                       url='http://www.example.com/'),))

    def test_close_open_square_brackets_inside_square_brackets(self):
        resp = self.ep.parse_markdown_v2("[inline ][ URL](http://www.example.com/)")

        assert resp == ('inline  URL', (MessageEntity(length=4,
                                                      offset=7,
                                                      type=MessageEntityType.TEXT_LINK,
                                                      url='http://www.example.com/'),))

    def test_open_close_parentheses_inside_square_brackets(self):
        with pytest.raises(BadMarkupException, match=re.escape(ERR_MSG_CHAR_MUST_BE_ESCAPED.format("("))):
            self.ep.parse_markdown_v2("[inline () URL](http://www.example.com/)")

    def test_close_open_parentheses_inside_square_brackets(self):
        with pytest.raises(BadMarkupException, match=re.escape(ERR_MSG_CHAR_MUST_BE_ESCAPED.format(")"))):
            self.ep.parse_markdown_v2("[inline )( URL](http://www.example.com/)")

    def test_newline_inside_entity(self):
        resp = self.ep.parse_markdown_v2("Test new line [inside \n inline URL](http://www.example.com/) text")
        assert resp == ('Test new line inside \n inline URL text',
                            (MessageEntity(length=19,
                                           offset=14,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://www.example.com/'),))

    def test_empty_entity(self):
        with pytest.raises(BadMarkupException, match=re.escape(ERR_TEXT_MUST_BE_NON_EMPTY)):
            self.ep.parse_markdown_v2("[]()")

    def test_empty_text_part(self):
        with pytest.raises(BadMarkupException, match=re.escape(ERR_TEXT_MUST_BE_NON_EMPTY)):
            self.ep.parse_markdown_v2("[](http://example.com)")

    def test_empty_url_part(self):
        resp = self.ep.parse_markdown_v2("[empty url]()")
        assert resp == ('empty url', ())

    @pytest.mark.xfail(reason="Wait for `check_and_normalize_url`. Issue#32")
    def test_without_url_part(self):
        resp = self.ep.parse_markdown_v2("[no url part at all]")
        assert resp == ('no url part at all', ())

    def test_nested_simple_entities(self):
        text = "A string with [*a* _nested_ ~enn~__ti__||ty||](http://outer.com)"
        resp = self.ep.parse_markdown_v2(text)
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
        text = "👨‍👩‍👧‍👦 😊😊 [A string with emojis 😊](ex.com) 😊😊"
        resp = self.ep.parse_markdown_v2(text)
        assert resp == ("👨‍👩‍👧‍👦 😊😊 A string with emojis 😊 😊😊",
                            (MessageEntity(length=23,
                                           offset=17,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://ex.com/'),))

    def test_non_latin_characters(self):
        resp = self.ep.parse_markdown_v2("[你好世界！](ex.com)")
        assert resp == ('你好世界！', (MessageEntity(length=5,
                                                    offset=0,
                                                    type=MessageEntityType.TEXT_LINK,
                                                    url='http://ex.com/'),))

