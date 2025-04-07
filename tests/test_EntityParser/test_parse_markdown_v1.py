import pytest
from telegram import MessageEntity
from telegram.constants import MessageEntityType

from constants import ERR_MSG_CANT_PARSE, ERR_MSG_EMPTY_STR
from ptbtest.entityparser import EntityParser
from ptbtest.errors import BadMarkupException


class TestBold:
    ep = EntityParser()

    def test_all_bold(self):
        resp = self.ep.parse_markdown("*hello world*")

        assert resp == ("hello world", (MessageEntity(length=11, offset=0, type=MessageEntityType.BOLD),))

    def test_at_the_beginning(self):
        resp = self.ep.parse_markdown("*hello* world")
        assert resp == ("hello world", (MessageEntity(length=5, offset=0, type=MessageEntityType.BOLD),))

    def test_at_the_end(self):
        resp = self.ep.parse_markdown("Bold text at *the end of the message*")
        assert resp == ("Bold text at the end of the message",
                        (MessageEntity(length=22, offset=13, type=MessageEntityType.BOLD),))

    def test_in_the_middle(self):
        resp = self.ep.parse_markdown("Bold text *in the middle* of the message")
        assert resp == ("Bold text in the middle of the message",
                        (MessageEntity(length=13, offset=10, type=MessageEntityType.BOLD),))

    def test_multiple_bold_parts(self):
        resp = self.ep.parse_markdown("Multiple *bold words* within *one message*.")
        assert resp == ("Multiple bold words within one message.",
                            (MessageEntity(length=10, offset=9, type=MessageEntityType.BOLD),
                            MessageEntity(length=11, offset=27, type=MessageEntityType.BOLD)))

    def test_multiline_multiple_bold_parts(self):
        resp = self.ep.parse_markdown('Multiple *lines*\nwith *bold * text.\nNo bold text here')
        assert resp == ("Multiple lines\nwith bold  text.\nNo bold text here",
                            (MessageEntity(length=5, offset=9, type=MessageEntityType.BOLD),
                             MessageEntity(length=5, offset=20, type=MessageEntityType.BOLD)))

    def test_escaped_symbol(self):
        resp = self.ep.parse_markdown("*Bold text* with an escaped \* symbol")
        assert resp == ("Bold text with an escaped * symbol",
                            (MessageEntity(length=9, offset=0, type=MessageEntityType.BOLD),))

    def test_escaped_symbol_inside_entity(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CANT_PARSE.format(offset=21)):
            self.ep.parse_markdown("An *escaped \* inside* entity")

    @pytest.mark.parametrize(["symbol", ], (("_", ), ("`", ), ("[", ), ("]",), ))
    def test_other_entity_symbols_inside_bold_entity(self, symbol):
        text = rf"A string with a *bold text and an escaped \{symbol} inside*."
        resp = self.ep.parse_markdown(text)
        assert resp == (f"A string with a bold text and an escaped \{symbol} inside.",
                            (MessageEntity(length=34, offset=16, type=MessageEntityType.BOLD),))

    def test_unclosed_entity(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CANT_PARSE.format(offset=5)):
            self.ep.parse_markdown("Test *unclosed entity")

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_outside_of_entity(self, symbol):
        text = f"{symbol*12}*bold text*{symbol*11}"
        resp = self.ep.parse_markdown(text)

        assert resp == ("bold text", (MessageEntity(length=9, offset=0, type=MessageEntityType.BOLD),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_entity(self, symbol):
        text = f"*{symbol*9}bold text{symbol*7}*"
        resp = self.ep.parse_markdown(text)

        assert resp ==  (f"{symbol*9}bold text",
                            (MessageEntity(length=18, offset=0, type=MessageEntityType.BOLD),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_entity_in_different_parts_of_the_message(self, symbol):
        text = "*hello\n\n\n\nworld\n\n\n\n\n*    *and one\nmore   \n\n\ntime\n\n   *"
        resp = self.ep.parse_markdown(text)

        assert resp ==  ("hello\n\n\n\nworld\n\n\n\n\n    and one\nmore   \n\n\ntime",
                            (MessageEntity(length=19, offset=0, type=MessageEntityType.BOLD),
                             MessageEntity(length=22, offset=23, type=MessageEntityType.BOLD)))

    def test_newline_inside_entity(self):
        resp = self.ep.parse_markdown("Test new line *inside\nentity* text")
        assert resp == ('Test new line inside\nentity text',
                            (MessageEntity(length=13, offset=14, type=MessageEntityType.BOLD),))


class TestItalic:
    ep = EntityParser()

    def test_all_italic(self):
        resp = self.ep.parse_markdown("_hello italic world_")

        assert resp == ("hello italic world", (MessageEntity(length=18, offset=0, type=MessageEntityType.ITALIC),))

    def test_at_the_beginning(self):
        resp = self.ep.parse_markdown("_hello_ italic world")
        assert resp == ("hello italic world", (MessageEntity(length=5, offset=0, type=MessageEntityType.ITALIC),))

    def test_at_the_end(self):
        resp = self.ep.parse_markdown("ITALIC text at _the end of the message_")
        assert resp == ("ITALIC text at the end of the message",
                        (MessageEntity(length=22, offset=15, type=MessageEntityType.ITALIC),))

    def test_in_the_middle(self):
        resp = self.ep.parse_markdown("ITALIC text _in the middle_ of the message")
        assert resp == ("ITALIC text in the middle of the message",
                        (MessageEntity(length=13, offset=12, type=MessageEntityType.ITALIC),))

    def test_multiple_italic_parts(self):
        resp = self.ep.parse_markdown("Multiple _ITALIC words_ within _one message_.")
        assert resp == ("Multiple ITALIC words within one message.",
                            (MessageEntity(length=12, offset=9, type=MessageEntityType.ITALIC),
                            MessageEntity(length=11, offset=29, type=MessageEntityType.ITALIC)))

    def test_multiline_multiple_bold_parts(self):
        resp = self.ep.parse_markdown('Multiple _lines_\nwith _ITALIC _ text.\nNo ITALIC text here')
        assert resp == ("Multiple lines\nwith ITALIC  text.\nNo ITALIC text here",
                            (MessageEntity(length=5, offset=9, type=MessageEntityType.ITALIC),
                             MessageEntity(length=7, offset=20, type=MessageEntityType.ITALIC)))

    def test_escaped_symbol(self):
        resp = self.ep.parse_markdown("_ITALIC text_ with an escaped \_ symbol")
        assert resp == ("ITALIC text with an escaped _ symbol",
                            (MessageEntity(length=11, offset=0, type=MessageEntityType.ITALIC),))


    def test_escaped_symbol_inside_entity(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CANT_PARSE.format(offset=21)):
            self.ep.parse_markdown("An _escaped \_ inside_ entity")

    @pytest.mark.parametrize(["symbol", ], (("*", ), ("`",), ("[",), ("]",), ))
    def test_other_entity_symbols_inside_italic_entity(self, symbol):
        text = rf"A string with a _ITALIC text and an escaped \{symbol} inside_."
        resp = self.ep.parse_markdown(text)
        assert resp == (f"A string with a ITALIC text and an escaped \{symbol} inside.",
                            (MessageEntity(length=36, offset=16, type=MessageEntityType.ITALIC),))

    def test_unclosed_entity(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CANT_PARSE.format(offset=5)):
            self.ep.parse_markdown("Test _unclosed entity")

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_outside_of_entity(self, symbol):
        text = f"{symbol*12}_italic text_{symbol*11}"
        resp = self.ep.parse_markdown(text)

        assert resp == ("italic text", (MessageEntity(length=11, offset=0, type=MessageEntityType.ITALIC),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_entity(self, symbol):
        text = f"_{symbol*9}italic text{symbol*7}_"
        resp = self.ep.parse_markdown(text)

        assert resp ==  (f"{symbol*9}italic text",
                            (MessageEntity(length=20, offset=0, type=MessageEntityType.ITALIC),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_entity_in_different_parts_of_the_message(self, symbol):
        text = "_hello\n\n\n\nworld\n\n\n\n\n_    _and one\nmore   \n\n\ntime\n\n   _"
        resp = self.ep.parse_markdown(text)

        assert resp ==  ("hello\n\n\n\nworld\n\n\n\n\n    and one\nmore   \n\n\ntime",
                             (MessageEntity(length=19, offset=0, type=MessageEntityType.ITALIC),
                              MessageEntity(length=22, offset=23, type=MessageEntityType.ITALIC)))

    def test_newline_inside_entity(self):
        resp = self.ep.parse_markdown("Test new line _inside\nentity_ text")
        assert resp == ('Test new line inside\nentity text',
                            (MessageEntity(length=13, offset=14, type=MessageEntityType.ITALIC),))


class TestInlineCode:
    ep = EntityParser()

    def test_all_inline_code(self):
        resp = self.ep.parse_markdown("`hello inline code world`")

        assert resp == ("hello inline code world", (MessageEntity(length=23, offset=0, type=MessageEntityType.CODE),))

    def test_at_the_beginning(self):
        resp = self.ep.parse_markdown("`hello` inline code world")
        assert resp == ("hello inline code world", (MessageEntity(length=5, offset=0, type=MessageEntityType.CODE),))

    def test_at_the_end(self):
        resp = self.ep.parse_markdown("inline code text at `the end of the message`")
        assert resp == ("inline code text at the end of the message",
                        (MessageEntity(length=22, offset=20, type=MessageEntityType.CODE),))

    def test_in_the_middle(self):
        resp = self.ep.parse_markdown("inline code text `in the middle` of the message")
        assert resp == ("inline code text in the middle of the message",
                        (MessageEntity(length=13, offset=17, type=MessageEntityType.CODE),))

    def test_multiple_inline_code_parts(self):
        resp = self.ep.parse_markdown("Multiple `inline code` within `parts`.")
        assert resp == ("Multiple inline code within parts.",
                            (MessageEntity(length=11, offset=9, type=MessageEntityType.CODE),
                             MessageEntity(length=5, offset=28, type=MessageEntityType.CODE)))

    def test_multiline_multiple_inline_code_parts(self):
        resp = self.ep.parse_markdown("Multiple `inline code`\nwith `coded` text.\nNo inline text here")
        assert resp == ("Multiple inline code\nwith coded text.\nNo inline text here",
                            (MessageEntity(length=11, offset=9, type=MessageEntityType.CODE),
                             MessageEntity(length=5, offset=26, type=MessageEntityType.CODE)))

    def test_escaped_symbol(self):
        resp = self.ep.parse_markdown("`inline code` with an escaped \` symbol")
        assert resp ==  ("inline code with an escaped ` symbol",
                            (MessageEntity(length=11, offset=0, type=MessageEntityType.CODE),))

    def test_escaped_symbol_inside_entity(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CANT_PARSE.format(offset=21)):
            self.ep.parse_markdown("An `escaped \` inside` entity")

    @pytest.mark.parametrize(["symbol", ], (("*",), ("_",), ("[",), ("]",), ))
    def test_other_entity_symbols_inside_italic_entity(self, symbol):
        text = rf"A string with an `inline code and an escaped \{symbol} inside`."
        resp = self.ep.parse_markdown(text)
        assert resp == (f"A string with an inline code and an escaped \{symbol} inside.",
                            (MessageEntity(length=36, offset=17, type=MessageEntityType.CODE),))

    def test_unclosed_entity(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CANT_PARSE.format(offset=5)):
            self.ep.parse_markdown("Test `unclosed entity")

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_outside_of_entity(self, symbol):
        text = f"{symbol*4}`inline code`{symbol*17}"
        resp = self.ep.parse_markdown(text)

        assert resp == ("inline code", (MessageEntity(length=11, offset=0, type=MessageEntityType.CODE),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_entity(self, symbol):
        text = f"`{symbol*10}inline code{symbol*18}`"
        resp = self.ep.parse_markdown(text)

        assert resp ==  (f"{symbol*10}inline code",
                            (MessageEntity(length=21, offset=0, type=MessageEntityType.CODE),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_entity_in_different_parts_of_the_message(self, symbol):
        text = "`hello\n\n\n\nworld\n\n\n\n\n`    `and one\nmore   \n\n\ntime\n\n   `"
        resp = self.ep.parse_markdown(text)

        assert resp ==  ("hello\n\n\n\nworld\n\n\n\n\n    and one\nmore   \n\n\ntime",
                            (MessageEntity(length=19, offset=0, type=MessageEntityType.CODE),
                             MessageEntity(length=22, offset=23, type=MessageEntityType.CODE)))

    def test_newline_inside_entity(self):
        resp = self.ep.parse_markdown("Test new line `inside\nentity` text")
        assert resp == ('Test new line inside\nentity text',
                            (MessageEntity(length=13, offset=14, type=MessageEntityType.CODE),))


class TestPreCode:
    ep = EntityParser()

    def test_all_pre_code(self):
        resp = self.ep.parse_markdown("```hello pre code world```")

        assert resp == (" pre code world",
                            (MessageEntity(language="hello", length=15, offset=0, type=MessageEntityType.PRE),))
        
    def test_pre_code_without_specified_language(self):
        resp = self.ep.parse_markdown("```\ni = 0\ni += 1```")
        assert resp == ("i = 0\ni += 1", (MessageEntity(length=12, offset=0, type=MessageEntityType.PRE),))

    def test_pre_code_with_specified_language_inline(self):
        resp = self.ep.parse_markdown("```python i = 0\ni += 1```")
        assert resp == (" i = 0\ni += 1",
                            (MessageEntity(language="python", length=13, offset=0, type=MessageEntityType.PRE),))

    def test_pre_code_with_specified_language_on_new_line(self):
        resp = self.ep.parse_markdown("```python\ni = 0\ni += 1```")
        assert resp == ("i = 0\ni += 1",
                            (MessageEntity(language="python", length=12, offset=0, type=MessageEntityType.PRE),))

    def test_pre_code_with_specified_language_with_multiple_new_lines_inbetween(self):
        resp = self.ep.parse_markdown("```python\n\n\n\ni = 0\ni += 1```")
        assert resp == ("\n\n\ni = 0\ni += 1",
                            (MessageEntity(language="python", length=15, offset=0, type=MessageEntityType.PRE),))

    @pytest.mark.parametrize(["lang", ], (("python", ), ("asm6502",), ("nand2tetris-hdl",),
                                         ("firestore-security-rules",), ("d",), ("avro-idl",)))
    def test_pre_code_with_different_languages(self, lang):
        resp_new_line = self.ep.parse_markdown(f"```{lang}\ni = 0\ni += 1```")
        assert resp_new_line == ("i = 0\ni += 1",
                                    (MessageEntity(language=f"{lang}", length=12, offset=0, type=MessageEntityType.PRE),))

        resp_with_whitespace = self.ep.parse_markdown(f"```{lang} i = 0\ni += 1```")
        assert resp_with_whitespace == (" i = 0\ni += 1",
                                            (MessageEntity(language=f"{lang}", length=13, offset=0, type=MessageEntityType.PRE),))

    def test_at_the_beginning(self):
        resp = self.ep.parse_markdown("```lua\nprint('hello\nworld')``` inline code world")
        assert resp == ("print('hello\nworld') inline code world",
                            (MessageEntity(language="lua", length=20, offset=0, type=MessageEntityType.PRE),))

    def test_at_the_end(self):
        resp = self.ep.parse_markdown("pre code at the end of the message ```lua\nprint('hello\nworld')```")
        assert resp == ("pre code at the end of the message print('hello\nworld')",
                            (MessageEntity(language="lua", length=20, offset=35, type=MessageEntityType.PRE),))

    def test_in_the_middle(self):
        resp = self.ep.parse_markdown("pre code text ```python i = 0\ni += 1``` of the message")
        assert resp == ("pre code text  i = 0\ni += 1 of the message",
                            (MessageEntity(language="python", length=13, offset=14, type=MessageEntityType.PRE),))

    def test_multiple_inline_code_parts(self):
        resp = self.ep.parse_markdown("Multiple code snippets ```python i = 0\ni += 1\n print(i)``` "
                                          "within one message ```lua\nprint('hello\nworld')```.")
        assert resp == ("Multiple code snippets  i = 0\ni += 1\n print(i) within one message print('hello\nworld').",
                            (MessageEntity(language="python", length=23, offset=23, type=MessageEntityType.PRE),
                             MessageEntity(language="lua", length=20, offset=66, type=MessageEntityType.PRE)))

    def test_multiline_multiple_inline_code_parts(self):
        text = ("A snippet number one: \n```python\ni = 11\ni -= 2\nprint(i)```\n\n"
                "A snippet number two: ```c\nint i = 0;\ni = i + 22;\n```\n\n")
        resp = self.ep.parse_markdown(text)

        assert resp == ('A snippet number one: \ni = 11\ni -= 2\nprint(i)\n\nA snippet number two: int i = 0;\ni = i + 22;',
                            (MessageEntity(language='python', length=22, offset=23, type=MessageEntityType.PRE),
                             MessageEntity(language='c', length=22, offset=69, type=MessageEntityType.PRE)))

    def test_escaped_symbol(self):
        resp = self.ep.parse_markdown("```lua i = 2\ni-2``` with an escaped \` symbol")
        assert resp ==  (' i = 2\ni-2 with an escaped ` symbol',
                         (MessageEntity(language='lua', length=10, offset=0, type=MessageEntityType.PRE),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_outside_of_entity(self, symbol):
        text = f"{symbol*2}```python def f(ch):\n    return ch*8```{symbol*3}"
        resp = self.ep.parse_markdown(text)

        assert resp == (' def f(ch):\n    return ch*8',
                            (MessageEntity(language='python', length=27, offset=0, type=MessageEntityType.PRE),))

    def test_with_leading_and_trailing_whitespace_inside_entity(self):
        symbol = " "
        text = f"```{symbol*6}python def f(ch):\n    return ch*8{symbol*23}```"
        resp = self.ep.parse_markdown(text)

        assert resp ==  ('      python def f(ch):\n    return ch*8',
                            (MessageEntity(length=39, offset=0, type=MessageEntityType.PRE),))

    def test_with_leading_and_trailing_newline_inside_entity(self):
        symbol = "\n"
        text = f"```{symbol*6}python def f(ch):\n    return ch*8{symbol*23}```"
        resp = self.ep.parse_markdown(text)

        assert resp ==  ('\n\n\n\n\npython def f(ch):\n    return ch*8',
                            (MessageEntity(length=38, offset=0, type=MessageEntityType.PRE),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_entity_in_different_parts_of_the_message(self, symbol):
        text = "```lua hello\n\n\n\nworld\n\n\n\n\n```    ```excel one\nmore   \n\n\ntime\n\n   ```"
        resp = self.ep.parse_markdown(text)

        assert resp ==  (' hello\n\n\n\nworld\n\n\n\n\n     one\nmore   \n\n\ntime',
                            (MessageEntity(language='lua', length=20, offset=0, type=MessageEntityType.PRE),
                             MessageEntity(language='excel', length=19, offset=24, type=MessageEntityType.PRE)))

    def test_escaped_symbol_inside_entity(self):
        resp = self.ep.parse_markdown("A snippet:```python escaped \` inside``` entity")

        assert resp == ('A snippet: escaped \\` inside entity',
                            (MessageEntity(language='python', length=18, offset=10, type=MessageEntityType.PRE),))

    @pytest.mark.parametrize(["symbol", ], ("*", "_", "[", "]", "`"))
    def test_entities_symbols_inside_pre_code_entity(self, symbol):
        text = rf"A string with a snippet ```d code snippet\nhere with escaped\n \{symbol} inside```."
        resp = self.ep.parse_markdown(text)
        assert resp == (f'A string with a snippet  code snippet\\nhere with escaped\\n \\{symbol} inside.',
                            (MessageEntity(language='d', length=44, offset=24, type=MessageEntityType.PRE),))

    def test_unclosed_entity(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CANT_PARSE.format(offset=5)):
            self.ep.parse_markdown("Test ```unclosed entity")


class TestInlineUrls:
    ep = EntityParser()

    def test_message_consists_of_one_entity_only(self):
        resp = self.ep.parse_markdown("[inline URL](http://www.example.com/)")

        entity = resp[1][0]
        assert resp == ('inline URL', (MessageEntity(length=10,
                                                     offset=0,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url='http://www.example.com/'),))
        assert entity.url == "http://www.example.com/"

    def test_at_the_beginning(self):
        resp = self.ep.parse_markdown("[hello](example.com/) world")
        entity = resp[1][0]

        assert resp ==  ('hello world', (MessageEntity(length=5,
                                                       offset=0,
                                                       type=MessageEntityType.TEXT_LINK,
                                                       url='http://example.com/'),))
        assert entity.url == "http://example.com/"

    def test_at_the_end(self):
        resp = self.ep.parse_markdown("Say '[hello](example.com)'")
        entity = resp[1][0]

        assert entity.url == "http://example.com/"
        assert resp ==  ("Say 'hello'", (MessageEntity(length=5,
                                                     offset=5,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url='http://example.com/'),))

    def test_in_the_middle(self):
        resp = self.ep.parse_markdown("URL [in the middle](https://example.com/login) of the message")
        entity = resp[1][0]

        assert entity.url == "https://example.com/login"

        assert resp == ('URL in the middle of the message', (MessageEntity(length=13,
                                                                           offset=4,
                                                                           type=MessageEntityType.TEXT_LINK,
                                                                           url='https://example.com/login'),))

    def test_multiple_inline_urls(self):
        resp = self.ep.parse_markdown("Multiple [inline urls](example.com/?param1=val1) "
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

    def test_multiline_multiple_bold_parts(self):
        resp = self.ep.parse_markdown('Multiple [inline urls](example.com/?param1=val1)\n'
                                      'in [one message](http://example.com/).\n'
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
        resp = self.ep.parse_markdown("A message with an [inline url](example.com/)"
                                      "and escaped symbols \[].")
        entity = resp[1][0]

        assert entity.url == "http://example.com/"

        assert resp ==  ('A message with an inline urland escaped symbols [].',
                            (MessageEntity(length=10,
                                           offset=18,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://example.com/'),))

    @pytest.mark.parametrize(["symbol", ], (("[", ), ("(", ), (")",), ))
    def test_inline_url_symbols_inside_entity(self, symbol):
        text = f"[inline {symbol} url](https://example.com/)"

        resp = self.ep.parse_markdown(text)
        entity = resp[1][0]

        assert entity.url == "https://example.com/"

        assert resp == (f'inline {symbol} url', (MessageEntity(length=12, offset=0, type=MessageEntityType.TEXT_LINK, url='https://example.com/'),))

    @pytest.mark.xfail(reason="Need to implement parse_url_entities")
    def test_closing_bracket_inside_entity(self):
        text = "[inline ] url](https://example.com/)"

        resp = self.ep.parse_markdown(text)
        entity = resp[1][0]

        assert entity.url == "https://example.com/"

        assert resp == ('inline  url](https://example.com/)',
                        (MessageEntity(length=20, offset=13, type=MessageEntityType.URL),))

    @pytest.mark.parametrize(["symbol", ], (("_", ), ("`", ), ("(", ), (")",), ("*",) ))
    def test_other_unescaped_entity_symbols_inside_inline_url(self, symbol):
        text = rf"A string with an [inline URL and unescaped '{symbol}'](http://www.example.com) in it."
        resp = self.ep.parse_markdown(text)

        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"

        assert resp == (f"A string with an inline URL and unescaped '{symbol}' in it.",
                        (MessageEntity(length=28,
                                       offset=17,
                                       type=MessageEntityType.TEXT_LINK,
                                       url='http://www.example.com/'),))

    def test_unclosed_square_brackets(self):
        with pytest.raises(BadMarkupException, match=ERR_MSG_CANT_PARSE.format(offset=5)):
            self.ep.parse_markdown("Test [unclosed entity(http://example.com)")

    def test_unclosed_parentheses(self):
        resp = self.ep.parse_markdown("[inline URL](http://www.example.com")
        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"

        assert resp == ('inline URL',
                            (MessageEntity(length=10,
                                           offset=0,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://www.example.com/'),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_outside_of_entity(self, symbol):
        resp = self.ep.parse_markdown(f"{symbol*8}[inline URL](http://www.example.com){symbol*33}")
        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"

        assert resp == ('inline URL', (MessageEntity(length=10,
                                                     offset=0,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url='http://www.example.com/'),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_square_brackets(self, symbol):
        resp = self.ep.parse_markdown(f"[{symbol*2}inline URL{symbol*14}](http://www.example.com)")
        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"

        assert resp == (f'{symbol*2}inline URL', (MessageEntity(length=12,
                                                                offset=0,
                                                                type=MessageEntityType.TEXT_LINK,
                                                                url='http://www.example.com/'),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_square_brackets_with_text_afterwards(self, symbol):
        resp = self.ep.parse_markdown(f"[{symbol*2}inline URL{symbol*14}](http://www.example.com) some text")
        entity = resp[1][0]
        assert entity.url == "http://www.example.com/"

        assert resp == (f'{symbol*2}inline URL{symbol*14} some text',
                            (MessageEntity(length=26,
                                           offset=0,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://www.example.com/'),))

    def test_trailing_whitespace_inside_square_brackets_with_text_after_entity(self):
        text = "A string with trailing whitespace [inside square brackets ](http://www.example.com)in it."
        resp = self.ep.parse_markdown(text)

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
        resp = self.ep.parse_markdown(input)
        assert resp == result

    @pytest.mark.xfail(reason="Need to implement parse_url_entities")
    def test_with_space_between_square_brackets_and_parentheses(self):
        resp = self.ep.parse_markdown("[inline URL] (http://www.example.com)")

        assert resp == ('inline URL (http://www.example.com)',
                            (MessageEntity(length=22, offset=12, type=MessageEntityType.URL),))

    @pytest.mark.xfail(reason="Need to implement parse_url_entities")
    def test_with_newline_between_square_brackets_and_parentheses(self):
        resp = self.ep.parse_markdown("[inline URL]\n(http://www.example.com)")

        assert resp == ('inline URL\n(http://www.example.com)',
                            (MessageEntity(length=22, offset=12, type=MessageEntityType.URL),))

    @pytest.mark.xfail(reason="Need to implement parse_url_entities")
    def test_with_space_between_square_brackets_and_parentheses_and_text_afterwards(self):
        resp = self.ep.parse_markdown("[inline URL] (http://www.example.com) some text here")

        assert resp == ('inline URL (http://www.example.com) some text here',
                        (MessageEntity(length=22, offset=12, type=MessageEntityType.URL),))

    @pytest.mark.parametrize(["symbol"], ((" ",), ("\n",)))
    def test_with_leading_and_trailing_whitespace_inside_entity_in_different_parts_of_the_message(self, symbol):
        text = "*hello\n\n\n\nworld\n\n\n\n\n*    *and one\nmore   \n\n\ntime\n\n   *"
        resp = self.ep.parse_markdown(text)

        assert resp ==  ("hello\n\n\n\nworld\n\n\n\n\n    and one\nmore   \n\n\ntime",
                            (MessageEntity(length=19, offset=0, type=MessageEntityType.BOLD),
                             MessageEntity(length=22, offset=23, type=MessageEntityType.BOLD)))

    @pytest.mark.parametrize(["url"], (("http://www.example.com/",),
                                       ("https://www.example.com/",),
                                       ("www.example.com/",),
                                       ("www.example.com",),
                                       ))
    def test_urls_without_path_and_params(self, url):
        resp = self.ep.parse_markdown(f"[inline URL]({url})")
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
        resp = self.ep.parse_markdown(f"[inline URL]({url}{path})")
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
        resp = self.ep.parse_markdown(f"[inline URL]({url})")
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
        resp = self.ep.parse_markdown(f"[inline URL]({url}{path})")
        protocol = "http"
        if url.startswith("https://"):
            protocol = "https"

        entity = resp[1][0]
        assert resp == ('inline URL', (MessageEntity(length=10,
                                                     offset=0,
                                                     type=MessageEntityType.TEXT_LINK,
                                                     url=f'{protocol}://example.com/'),))
        assert entity.url == f'{protocol}://example.com/{path}'

    @pytest.mark.xfail(reason="Need to implement parse_url_entities")
    def test_open_close_square_brackets_inside_square_brackets(self):
        resp = self.ep.parse_markdown("[inline [] URL](http://www.example.com/)")

        assert resp == ('inline [ URL](http://www.example.com/)',
                        (MessageEntity(length=23, offset=14, type=MessageEntityType.URL),))

    def test_close_open_square_brackets_inside_square_brackets(self):
        resp = self.ep.parse_markdown("[inline ][ URL](http://www.example.com/)")

        assert resp == ('inline  URL', (MessageEntity(length=4,
                                                      offset=7,
                                                      type=MessageEntityType.TEXT_LINK,
                                                      url='http://www.example.com/'),))

    def test_open_close_parentheses_inside_square_brackets(self):
        resp = self.ep.parse_markdown("[inline () URL](http://www.example.com/)")

        assert resp == ('inline () URL', (MessageEntity(length=13,
                                                        offset=0,
                                                        type=MessageEntityType.TEXT_LINK,
                                                        url='http://www.example.com/'),))

    def test_close_open_parentheses_inside_square_brackets(self):
        resp = self.ep.parse_markdown("[inline )( URL](http://www.example.com/)")

        assert resp == ('inline )( URL', (MessageEntity(length=13,
                                                        offset=0,
                                                        type=MessageEntityType.TEXT_LINK,
                                                        url='http://www.example.com/'),))

    def test_newline_inside_entity(self):
        resp = self.ep.parse_markdown("Test new line [inside \n inline URL](http://www.example.com/) text")
        assert resp == ('Test new line inside \n inline URL text',
                            (MessageEntity(length=19,
                                           offset=14,
                                           type=MessageEntityType.TEXT_LINK,
                                           url='http://www.example.com/'),))

    def test_empty_entity(self):
        resp = self.ep.parse_markdown("[]()")
        assert resp == ('()', ())


class TestEmptyEntities:
    ep = EntityParser()

    @pytest.mark.parametrize(["input"], (("*  *    ** **    ", ),
                                         ("_   _ _  _            __", ),
                                         ( "```    \n\n  ```",),
                                         ("  ```python    \n\n  ``` ```    ```   ", ),
                                         ("` `  `` `          `     ``",),
                                         ("** __ `` ```lua\n``` * * _   _    `     \n\n\n`",),
                                         ("*\n* _\n_ `\n`",),
                                         ))
    def test_empty_entity_and_empty_message(self, input):
        with pytest.raises(BadMarkupException, match=ERR_MSG_EMPTY_STR):
            self.ep.parse_markdown(input)

    @pytest.mark.parametrize(["input", "result"], (
            ("*  *    text **    ", ('      text', (MessageEntity(length=2, offset=0, type=MessageEntityType.BOLD),))),
            ("    _   _ text __ ", ('    text', (MessageEntity(length=3, offset=0, type=MessageEntityType.ITALIC),))),
            ("`    `  text `   ` text ``", ('      text     text', (MessageEntity(length=4, offset=0, type=MessageEntityType.CODE),
                                                                    MessageEntity(length=3, offset=11, type=MessageEntityType.CODE)))),
            ("```python\n\n\n``` text ``````", ('\n\n text', (MessageEntity(language='python', length=2, offset=0, type=MessageEntityType.PRE),)))
    ))
    def test_empty_entity_with_text(self, input, result):
        resp = self.ep.parse_markdown(input)
        assert resp == result


class TestMisc:
    ep = EntityParser()

    def test_inline_mention(self):
        # By some reason Markdown V1 ignores inline mentions. E.g.,
        # [inline mention of a user](tg://user?id=123456789)
        resp = self.ep.parse_markdown("[inline mention of a user](tg://user?id=123456789)")

        assert resp == ('inline mention of a user', ())

    def test_multiple_entities_in_text(self):
        text = ('*bold text*\n_italic text_\n[inline URL](http://www.example.com/)\n'
                '[inline mention of a user](tg://user?id=123456789)\n'
                '`inline fixed-width code`\n```\npre-formatted fixed-width code block\n```'
                '\n```python\npre-formatted fixed-width code block written in the '
                'Python programming language\n```')

        resp = self.ep.parse_markdown(text)

        assert resp == ('bold text\nitalic text\ninline URL\ninline mention of a user\ninline fixed-width code\n'
                        'pre-formatted fixed-width code block\n\npre-formatted fixed-width code block written in '
                        'the Python programming language',
                            (MessageEntity(length=9, offset=0, type=MessageEntityType.BOLD),
                             MessageEntity(length=11, offset=10, type=MessageEntityType.ITALIC),
                             MessageEntity(length=10, offset=22, type=MessageEntityType.TEXT_LINK, url='http://www.example.com/'),
                             MessageEntity(length=23, offset=58, type=MessageEntityType.CODE),
                             MessageEntity(length=37, offset=82, type=MessageEntityType.PRE),
                             MessageEntity(language='python', length=79, offset=120, type=MessageEntityType.PRE)))

    @pytest.mark.parametrize("input, result", (("[no parentheses]", "no parentheses"),
                                               ("[ no parentheses ]", "no parentheses"),
                                               ("[no parentheses ]", "no parentheses"),
                                               ("[no parentheses ] some trailing text", "no parentheses  some trailing text"),
                                               ("[ no parentheses ] some trailing text", "no parentheses  some trailing text"),
                                               ("some leading text [ no parentheses ] some trailing text", "some leading text  no parentheses  some trailing text"),
    ))
    def test_square_brackets_without_parentheses(self, input, result):
        resp = self.ep.parse_markdown(input)

        assert resp == (result, ())

    @pytest.mark.parametrize("input, offset", (("A", 24), ("©", 25), ("😊", 27)))
    def test_error_message_with_different_characters(self, input, offset):
        text = f"Text with '{input}' and broken*entity"
        with pytest.raises(BadMarkupException, match=ERR_MSG_CANT_PARSE.format(offset=offset)):
            self.ep.parse_markdown(text)
