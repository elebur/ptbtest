import re

import pytest
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


class TestInlineMention:
    """
    Inline mentioning doesn't work with Markdown V2
    """
    ep = EntityParser()
    def test_inline_mention(self):
        resp = self.ep.parse_markdown_v2("[inline mention of a user](tg://user?id=1234)")
        assert resp == ("inline mention of a user", ())


class TestCustomEmoji:
    @pytest.mark.xfail(reason="Need purchased @username")
    def test_custom_emoji(self):
        """
        Custom emoji entities can only be used by bots
        that purchased additional usernames on Fragment,
        https://fragment.com/?filter=sale
        """
        assert 1 == 2, "Need purchased @username"


class TestPre:
    ep = EntityParser()
    def test_pre_on_one_line(self):
        template = "A single line string with pre ```lua hello world```"
        resp = self.ep.parse_markdown_v2(template)

        entity = resp[1][0]

        assert entity.language == "lua"
        assert resp == ("A single line string with pre  hello world",
                            (MessageEntity(language="lua",
                                           length=12,
                                           offset=30,
                                           type=MessageEntityType.PRE),))

    def test_pre_on_one_line_with_one_word(self):
        resp = self.ep.parse_markdown_v2("```onelinepreentity```")

        entity = resp[1][0]

        assert entity.language is None
        assert resp == ("onelinepreentity", (MessageEntity(length=16,
                                                           offset=0,
                                                           type=MessageEntityType.PRE),))

    def test_pre_on_multiple_lines(self):
        template = "A single \nline string with pre ```bash \nhello\n world```"
        resp = self.ep.parse_markdown_v2(template)

        entity = resp[1][0]

        assert entity.language == "bash"
        assert resp == ("A single \nline string with pre  \nhello\n world",
                            (MessageEntity(language="bash",
                                           length=14,
                                           offset=31,
                                           type=MessageEntityType.PRE),))

    @pytest.mark.parametrize(["escaped_char"], (RESERVED_ENTITY_CHARS +
                                                RESERVED_REGULAR_CHARS +
                                                "|\|" + "_\_"))
    def test_pre_with_escaped_char_in_it(self, escaped_char):
        template = (f"A multiline string with ```entity\n"
                    rf"and escaped char \{escaped_char} within``` the entity")

        resp = self.ep.parse_markdown_v2(template)
        entity = resp[1][0]

        assert entity.language == "entity"
        assert resp == (f"A multiline string with and escaped char {escaped_char} within the entity",
                        (MessageEntity(language="entity",
                                       length=25,
                                       offset=24,
                                       type=MessageEntityType.PRE),))

    @pytest.mark.parametrize(["e_char"], (("*",),("_",),("__",),("~",),("||",),))
    def test_with_unescaped_entities(self, e_char):
        text = f"```python code {e_char}with unescaped entities{e_char} inside```"
        resp = self.ep.parse_markdown_v2(text)
        length = 38
        if len(e_char) == 2:
            length += 2

        entity = resp[1][0]

        assert entity.language == "python"
        assert resp == (f" code {e_char}with unescaped entities{e_char} inside",
                        (MessageEntity(language="python", length=length, offset=0, type=MessageEntityType.PRE),))

    @pytest.mark.parametrize(["e_char"], (("\*",),("\_",),("\_\_",),("\~",),("\|\|",),("\`",)))
    def test_with_escaped_entities(self, e_char):
        text = f"```python code {e_char}with unescaped entities{e_char} inside```"
        resp = self.ep.parse_markdown_v2(text)
        length = 38
        if len(e_char) == 4:
            length += 2
        ch = e_char.replace("\\", "")
        assert resp == (f" code {ch}with unescaped entities{ch} inside",
                        (MessageEntity(language="python", length=length, offset=0,
                                       type=MessageEntityType.PRE),))

        entity = resp[1][0]
        assert entity.language == "python"


    @pytest.mark.parametrize(["char"], "abc,?&#@")
    def test_with_escaped_ascii(self, char):
        text = rf"```lua code with an escaped ASCII character \{char}```"
        resp = self.ep.parse_markdown_v2(text)

        entity = resp[1][0]
        assert entity.language == "lua"
        assert resp == (f" code with an escaped ASCII character {char}",
                        (MessageEntity(language="lua", length=39, offset=0,
                                       type=MessageEntityType.PRE),))

    @pytest.mark.parametrize(["char"], "€À÷ÿЙ")
    def test_with_escaped_non_ascii(self, char):
        text = rf"```lua code with an escaped non\-ASCII character \{char}```"
        resp = self.ep.parse_markdown_v2(text)

        entity = resp[1][0]
        assert entity.language == "lua"
        assert resp == (f" code with an escaped non-ASCII character \\{char}",
                        (MessageEntity(language="lua", length=44, offset=0,
                                       type=MessageEntityType.PRE),))

    def test_with_escaped_whitespace(self):
        text = rf"```lua code with an escaped ASCII character \ ```"
        resp = self.ep.parse_markdown_v2(text)

        entity = resp[1][0]
        assert entity.language == "lua"
        assert resp == (" code with an escaped ASCII character",
                        (MessageEntity(language="lua", length=37,
                                       offset=0, type=MessageEntityType.PRE),))

    def test_pre_without_lang(self):
        resp1 = self.ep.parse_markdown_v2("```\ncode\nsnippet without\nlanguage```")

        entity = resp1[1][0]
        assert entity.language is None
        assert resp1 == ("code\nsnippet without\nlanguage",
                         (MessageEntity(length=29, offset=0, type=MessageEntityType.PRE),))

        resp2 = self.ep.parse_markdown_v2("Leading text```\ncode\nsnippet without\nlanguage```")

        entity2 = resp2[1][0]
        assert entity2.language is None
        assert resp2 == ("Leading textcode\nsnippet without\nlanguage",
                         (MessageEntity(length=29, offset=12, type=MessageEntityType.PRE),))

    def test_language_without_content(self):
        with pytest.raises(BadMarkupException, match="Text must be non\-empty"):
            self.ep.parse_markdown_v2("```lua ```")

    def test_all_pre_code(self):
        resp = self.ep.parse_markdown_v2("```hello pre code world```")

        entity = resp[1][0]
        assert entity.language == "hello"
        assert resp == (" pre code world",
                        (MessageEntity(language="hello", length=15, offset=0, type=MessageEntityType.PRE),))

    def test_pre_code_without_specified_language(self):
        resp = self.ep.parse_markdown_v2("```\ni = 0\ni += 1```")

        entity = resp[1][0]
        assert entity.language is None
        assert resp == ("i = 0\ni += 1", (MessageEntity(length=12, offset=0,
                                                        type=MessageEntityType.PRE),))

    def test_pre_code_with_specified_language_inline(self):
        resp = self.ep.parse_markdown_v2("```python i = 0\ni += 1```")

        entity = resp[1][0]
        assert entity.language == "python"
        assert resp == (" i = 0\ni += 1",
                        (MessageEntity(language="python", length=13,
                                       offset=0, type=MessageEntityType.PRE),))

    def test_pre_code_with_specified_language_on_new_line(self):
        resp = self.ep.parse_markdown_v2("```python\ni = 0\ni += 1```")

        entity = resp[1][0]
        assert entity.language == "python"
        assert resp == ("i = 0\ni += 1",
                        (MessageEntity(language="python", length=12,
                                       offset=0, type=MessageEntityType.PRE),))

    def test_pre_code_with_specified_language_with_multiple_new_lines_inbetween(self):
        resp = self.ep.parse_markdown_v2("```python\n\n\n\ni = 0\ni += 1```")

        entity = resp[1][0]
        assert entity.language == "python"
        assert resp == ("\n\n\ni = 0\ni += 1",
                        (MessageEntity(language="python", length=15, offset=0, type=MessageEntityType.PRE),))

    @pytest.mark.parametrize(["lang", ], (("python",), ("asm6502",), ("nand2tetris-hdl",),
                                          ("firestore-security-rules",), ("d",), ("avro-idl",)))
    def test_pre_code_with_different_languages(self, lang):
        resp_new_line = self.ep.parse_markdown_v2(f"```{lang}\ni = 0\ni += 1```")

        entity_newline = resp_new_line[1][0]
        assert entity_newline.language == lang
        assert resp_new_line == ("i = 0\ni += 1",
                                 (MessageEntity(language=f"{lang}", length=12,
                                                offset=0, type=MessageEntityType.PRE),))

        resp_whitespace = self.ep.parse_markdown_v2(f"```{lang} i = 0\ni += 1```")
        entity_whitespace = resp_whitespace[1][0]
        assert entity_whitespace.language == lang
        assert resp_whitespace == (" i = 0\ni += 1",
                                   (MessageEntity(language=f"{lang}", length=13,
                                                  offset=0, type=MessageEntityType.PRE),))

    def test_at_the_beginning(self):
        resp = self.ep.parse_markdown_v2("```lua\nprint('hello\nworld')``` inline code world")

        entity = resp[1][0]
        assert entity.language == "lua"
        assert resp == ("print('hello\nworld') inline code world",
                        (MessageEntity(language="lua", length=20,
                                       offset=0, type=MessageEntityType.PRE),))

    def test_at_the_end(self):
        resp = self.ep.parse_markdown_v2("pre code at the end of the message ```lua\nprint('hello\nworld')```")
        entity = resp[1][0]
        assert entity.language == "lua"
        assert resp == ("pre code at the end of the message print('hello\nworld')",
                        (MessageEntity(language="lua", length=20,
                                       offset=35, type=MessageEntityType.PRE),))

    def test_in_the_middle(self):
        resp = self.ep.parse_markdown_v2("pre code text ```python i = 0\ni += 1``` of the message")
        entity = resp[1][0]
        assert entity.language == "python"
        assert resp == ("pre code text  i = 0\ni += 1 of the message",
                        (MessageEntity(language="python", length=13,
                                       offset=14, type=MessageEntityType.PRE),))

    def test_multiple_inline_code_parts(self):
        resp = self.ep.parse_markdown_v2("Multiple code snippets ```python i = 0\ni += 1\n print(i)``` "
                                      "within one message ```lua\nprint('hello\nworld')```\.")

        entity1 = resp[1][0]
        assert entity1.language == "python"

        entity2 = resp[1][1]
        assert entity2.language == "lua"

        assert resp == ("Multiple code snippets  i = 0\ni += 1\n print(i) within one message print('hello\nworld').",
                        (MessageEntity(language="python", length=23, offset=23, type=MessageEntityType.PRE),
                         MessageEntity(language="lua", length=20, offset=66, type=MessageEntityType.PRE)))

    def test_multiline_multiple_inline_code_parts(self):
        text = ("A snippet number one: \n```python\ni = 11\ni -= 2\nprint(i)```\n\n"
                "A snippet number two: ```c\nint i = 0;\ni = i + 22;\n```\n\n")
        resp = self.ep.parse_markdown_v2(text)

        entity1 = resp[1][0]
        assert entity1.language == "python"

        entity2 = resp[1][1]
        assert entity2.language == "c"

        assert resp == (
        "A snippet number one: \ni = 11\ni -= 2\nprint(i)\n\nA snippet number two: int i = 0;\ni = i + 22;",
        (MessageEntity(language="python", length=22, offset=23, type=MessageEntityType.PRE),
         MessageEntity(language="c", length=22, offset=69, type=MessageEntityType.PRE)))

    def test_escaped_backquote_symbol(self):
        resp = self.ep.parse_markdown_v2("```lua i = 2\ni-2``` with an escaped \` symbol")
        entity = resp[1][0]
        assert entity.language == "lua"
        assert resp == (" i = 2\ni-2 with an escaped ` symbol",
                        (MessageEntity(language="", length=10, offset=0, type=MessageEntityType.PRE),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_outside_of_entity(self, symbol):
        text = f"{symbol * 2}```python def f(ch):\n    return ch*8```{symbol * 3}"
        resp = self.ep.parse_markdown_v2(text)

        entity = resp[1][0]
        assert entity.language == "python"
        assert resp == (" def f(ch):\n    return ch*8",
                        (MessageEntity(language="", length=27, offset=0, type=MessageEntityType.PRE),))

    def test_with_leading_and_trailing_whitespace_inside_entity(self):
        symbol = " "
        text = f"```{symbol * 6}python def f(ch):\n    return ch*8{symbol * 23}```"
        resp = self.ep.parse_markdown_v2(text)

        entity = resp[1][0]
        assert entity.language is None
        assert resp == ("      python def f(ch):\n    return ch*8",
                        (MessageEntity(length=39, offset=0, type=MessageEntityType.PRE),))

    def test_with_leading_and_trailing_newline_inside_entity(self):
        symbol = "\n"
        text = f"```{symbol * 6}python def f(ch):\n    return ch*8{symbol * 23}```"
        resp = self.ep.parse_markdown_v2(text)

        entity = resp[1][0]
        assert entity.language is None
        assert resp == ("\n\n\n\n\npython def f(ch):\n    return ch*8",
                        (MessageEntity(length=38, offset=0, type=MessageEntityType.PRE),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_entity_in_different_parts_of_the_message(self, symbol):
        text = "```lua hello\n\n\n\nworld\n\n\n\n\n```    ```excel one\nmore   \n\n\ntime\n\n   ```"
        resp = self.ep.parse_markdown_v2(text)

        entity1 = resp[1][0]
        assert entity1.language == "lua"

        entity2 = resp[1][1]
        assert entity2.language == "excel"
        assert resp == (" hello\n\n\n\nworld\n\n\n\n\n     one\nmore   \n\n\ntime",
                        (MessageEntity(language="lua", length=20, offset=0, type=MessageEntityType.PRE),
                         MessageEntity(language="excel", length=19, offset=24, type=MessageEntityType.PRE)))

    def test_unclosed_entity(self):
        msg = ERR_MSG_CANT_PARSE_ENTITY.format(offset=5, entity_type="precode")
        with pytest.raises(BadMarkupException, match=msg):
            self.ep.parse_markdown_v2("Test ```unclosed entity")

    def test_unclosed_with_single_backquote_at_the_end(self):
        msg = ERR_MSG_CANT_PARSE_ENTITY.format(offset=59, entity_type="code")
        with pytest.raises(BadMarkupException, match=msg):
            self.ep.parse_markdown_v2(" ```unclosed pre entity with one single backquote at the end`")


class TestBlockquote:
    ep = EntityParser()
    def test_one_line_blockquote(self):
        text = ">Block quotation started"
        resp = self.ep.parse_markdown_v2(text)

        assert resp == ('Block quotation started',
                            (MessageEntity(length=23, offset=0,
                                           type=MessageEntityType.BLOCKQUOTE),))

    def test_only_blockquote_in_message(self):
        text = (">Block quotation started\n"
                ">Block quotation continued\n"
                ">Block quotation continued\n"
                ">Block quotation continued\n"
                ">The last line of the block quotation")

        resp = self.ep.parse_markdown_v2(text)
        assert resp == ("Block quotation started\n"
                        "Block quotation continued\n"
                        "Block quotation continued\n"
                        "Block quotation continued\n"
                        "The last line of the block quotation",
                            (MessageEntity(length=138,
                                           offset=0,
                                           type=MessageEntityType.BLOCKQUOTE),))

    def test_multiple_blockquotes_split_by_newline(self):
        text = (">Block quotation started\n"
                ">Block quotation continued\n"
                "\n"
                ">Block quotation continued\n"
                ">Block quotation continued\n"
                ">The last line of the block quotation")

        resp = self.ep.parse_markdown_v2(text)
        assert resp == ("Block quotation started\n"
                        "Block quotation continued\n"
                        "\n"
                        "Block quotation continued\n"
                        "Block quotation continued\n"
                        "The last line of the block quotation",
                            (MessageEntity(length=50, offset=0,
                                           type=MessageEntityType.BLOCKQUOTE),
                             MessageEntity(length=88, offset=51,
                                           type=MessageEntityType.BLOCKQUOTE)))

    @pytest.mark.parametrize(["entity"], (("*",), ("```",), ("__",),
                                                ("~",), ("||",), ("`",), ))
    def test_multiple_blockquotes_split_by_another_entity(self, entity):
        text = (">Block quotation started\n"
                ">Block quotation continued\n"
                f"{entity}{entity}"
                ">Block quotation continued\n"
                ">Block quotation continued\n"
                ">The last line of the block quotation")

        resp = self.ep.parse_markdown_v2(text)
        assert resp == ("Block quotation started\n"
                        "Block quotation continued\n"
                        "Block quotation continued\n"
                        "Block quotation continued\n"
                        "The last line of the block quotation",
                            (MessageEntity(length=50, offset=0,
                                           type=MessageEntityType.BLOCKQUOTE),
                             MessageEntity(length=88, offset=50,
                                           type=MessageEntityType.BLOCKQUOTE)))

    def test_expandable_blockquote(self):
        text = (">Block quotation started\n"
                ">Block quotation continued\n"
                ">Block quotation continued\n"
                ">Block quotation continued\n"
                ">The last line of the block quotation||")

        resp = self.ep.parse_markdown_v2(text)
        assert resp == ('Block quotation started\n'
                        'Block quotation continued\n'
                        'Block quotation continued\n'
                        'Block quotation continued\n'
                        'The last line of the block quotation',
                            (MessageEntity(length=138, offset=0,
                                           type=MessageEntityType.EXPANDABLE_BLOCKQUOTE),))
    def test_nested_entities(self):
        text = ('>||Block|| *quotation* _started_\n'
                '>__Block__ `quotation` ~ontinued~\n'
                '>```block quotation continued```\n'
                '>[Block](http://google.com) quotation continued\n'
                '>The last line of the block quotation')

        resp = self.ep.parse_markdown_v2(text)
        assert resp == ("Block quotation started\n"
                        "Block quotation ontinued\n"
                        " quotation continued\n"
                        "Block quotation continued\n"
                        "The last line of the block quotation",
                            (MessageEntity(length=132, offset=0, type=MessageEntityType.BLOCKQUOTE),
                             MessageEntity(length=5, offset=0, type=MessageEntityType.SPOILER),
                             MessageEntity(length=9, offset=6, type=MessageEntityType.BOLD),
                             MessageEntity(length=7, offset=16, type=MessageEntityType.ITALIC),
                             MessageEntity(length=5, offset=24, type=MessageEntityType.UNDERLINE),
                             MessageEntity(length=9, offset=30, type=MessageEntityType.CODE),
                             MessageEntity(length=8, offset=40, type=MessageEntityType.STRIKETHROUGH),
                             MessageEntity(language="block", length=20, offset=49, type=MessageEntityType.PRE),
                             MessageEntity(length=5, offset=70,
                                           type=MessageEntityType.TEXT_LINK, url="http://google.com/")))
    @pytest.mark.parametrize("e_char, e_type", (
            ("*", MessageEntityType.BOLD),
            ("_", MessageEntityType.ITALIC),
            ("__", MessageEntityType.UNDERLINE),
            ("~", MessageEntityType.STRIKETHROUGH),
            ("||", MessageEntityType.SPOILER),
            ("`", MessageEntityType.CODE),
    ))
    def test_unescaped_entity_char(self, e_char, e_type):
        text = (f">Block {e_char}quotation started\n"
                ">Block quotation continued\n")
        msg = ERR_MSG_CANT_PARSE_ENTITY.format(entity_type=e_type,
                                               offset=7)
        with pytest.raises(BadMarkupException, match=msg):
            self.ep.parse_markdown_v2(text)

    @pytest.mark.parametrize(["char"], RESERVED_REGULAR_CHARS)
    def test_unescaped_regular_char(self, char):
        text = (f">Block {char}quotation started\n"
                ">Block quotation continued\n")
        msg = ERR_MSG_CHAR_MUST_BE_ESCAPED.format(char)
        with pytest.raises(BadMarkupException, match=re.escape(msg)):
            self.ep.parse_markdown_v2(text)
