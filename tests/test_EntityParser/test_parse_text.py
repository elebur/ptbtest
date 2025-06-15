import pytest
from telegram import MessageEntity
from telegram.constants import MessageEntityType, ParseMode

from ptbtest import BadMarkupException
from ptbtest.entityparser import EntityParser

class TestParseTextNoMarkup:
    # [S]ystem [u]nder [t]est
    sut = lambda self, text: EntityParser().parse_text(text)  # noqa: E731

    def test_non_intersected_entities(self):
        test_text = ("Test text @without /markup but with #other kinds "
                     "of entities $ABC +1123456789 tg://resolve?domain=username "
                     "http://example.com google.com")

        resp_text, entities = self.sut(test_text)

        assert entities == (MessageEntity(length=8, offset=10, type=MessageEntityType.MENTION),
                            MessageEntity(length=7, offset=19, type=MessageEntityType.BOT_COMMAND),
                            MessageEntity(length=6, offset=36, type=MessageEntityType.HASHTAG),
                            MessageEntity(length=4, offset=61, type=MessageEntityType.CASHTAG),
                            MessageEntity(length=28, offset=78, type=MessageEntityType.URL),
                            MessageEntity(length=18, offset=107, type=MessageEntityType.URL),
                            MessageEntity(length=10, offset=126, type=MessageEntityType.URL))

    def test_intersected_entities(self):
        test_text = "https://@example.com/#hashtag  +18001234567@email.com"

        text, entities = self.sut(test_text)
        assert text == "https://@example.com/#hashtag  +18001234567@email.com"
        assert entities == (MessageEntity(length=8, offset=8, type=MessageEntityType.MENTION),
                            MessageEntity(length=8, offset=21, type=MessageEntityType.HASHTAG),
                            MessageEntity(length=22, offset=31, type=MessageEntityType.EMAIL))


class TestParseTextWithMarkup:
    sut = lambda self, text, markup: EntityParser().parse_text(text, markup)  # noqa: E731
    entities = {
        "b": MessageEntityType.BOLD,
        "strong": MessageEntityType.BOLD,
        "i": MessageEntityType.ITALIC,
        "em": MessageEntityType.ITALIC,
        "s": MessageEntityType.STRIKETHROUGH,
        "strike": MessageEntityType.STRIKETHROUGH,
        "del": MessageEntityType.STRIKETHROUGH,
        "u": MessageEntityType.UNDERLINE,
        "ins": MessageEntityType.UNDERLINE,
        "tg-spoiler": MessageEntityType.SPOILER,
        "*": MessageEntityType.BOLD,
        "_": MessageEntityType.ITALIC,
        "~": MessageEntityType.STRIKETHROUGH,
        "__": MessageEntityType.UNDERLINE,
        "||": MessageEntityType.SPOILER,
    }

    @pytest.mark.parametrize(["tag"], (("b", ), ("strong", ), ("i", ), ("em", ),
                                       ("s", ), ("strike", ), ("del", ), ("u", ),
                                       ("ins", ), ("tg-spoiler", )))
    def test_inside_simple_entity(self, tag):
        test_text = (f"<{tag}>Some text with @mention #hashtag $CASH "
                f"/command email@example.com +18001234567</{tag}>")

        text, entities = self.sut(test_text, ParseMode.HTML)
        assert text == "Some text with @mention #hashtag $CASH /command email@example.com +18001234567"
        assert entities == (MessageEntity(length=15, offset=0, type=self.entities[tag]),
                            MessageEntity(length=8, offset=15, type=MessageEntityType.MENTION),
                            MessageEntity(length=8, offset=15, type=self.entities[tag]),
                            MessageEntity(length=1, offset=23, type=self.entities[tag]),
                            MessageEntity(length=8, offset=24, type=MessageEntityType.HASHTAG),
                            MessageEntity(length=8, offset=24, type=self.entities[tag]),
                            MessageEntity(length=1, offset=32, type=self.entities[tag]),
                            MessageEntity(length=5, offset=33, type=MessageEntityType.CASHTAG),
                            MessageEntity(length=5, offset=33, type=self.entities[tag]),
                            MessageEntity(length=1, offset=38, type=self.entities[tag]),
                            MessageEntity(length=8, offset=39, type=MessageEntityType.BOT_COMMAND),
                            MessageEntity(length=8, offset=39, type=self.entities[tag]),
                            MessageEntity(length=1, offset=47, type=self.entities[tag]),
                            MessageEntity(length=17, offset=48, type=MessageEntityType.EMAIL),
                            MessageEntity(length=17, offset=48, type=self.entities[tag]),
                            MessageEntity(length=1, offset=65, type=self.entities[tag]),
                            MessageEntity(length=12, offset=66, type=MessageEntityType.PHONE_NUMBER),
                            MessageEntity(length=12, offset=66, type=self.entities[tag]))

    def test_simple_entity_divided_by_markup_entities(self):
        test_text = ("Some text with <b>@men</b>tion <i>#hash</i>tag <em>$CA</em>SH"
                " <ins>/comm</ins>and <del>email@exa</del>mple.com +18001234567")

        text, entities = self.sut(test_text, ParseMode.HTML)

        assert text == "Some text with @mention #hashtag $CASH /command email@example.com +18001234567"
        assert entities == (MessageEntity(length=8, offset=15, type=MessageEntityType.MENTION),
                            MessageEntity(length=4, offset=15, type=MessageEntityType.BOLD),
                            MessageEntity(length=8, offset=24, type=MessageEntityType.HASHTAG),
                            MessageEntity(length=5, offset=24, type=MessageEntityType.ITALIC),
                            MessageEntity(length=5, offset=33, type=MessageEntityType.CASHTAG),
                            MessageEntity(length=3, offset=33, type=MessageEntityType.ITALIC),
                            MessageEntity(length=8, offset=39, type=MessageEntityType.BOT_COMMAND),
                            MessageEntity(length=5, offset=39, type=MessageEntityType.UNDERLINE),
                            MessageEntity(length=17, offset=48, type=MessageEntityType.EMAIL),
                            MessageEntity(length=9, offset=48, type=MessageEntityType.STRIKETHROUGH),
                            MessageEntity(length=12, offset=66, type=MessageEntityType.PHONE_NUMBER))

    def test_inside_nested_markup(self):
        test_text = "*Bold @mention with _italic \#hastag_ and __underlined email@example\.com__*"  # noqa: W605

        text, entities = self.sut(test_text, ParseMode.MARKDOWN_V2)
        assert text == "Bold @mention with italic #hastag and underlined email@example.com"
        assert entities == (MessageEntity(length=5, offset=0, type=MessageEntityType.BOLD),
                            MessageEntity(length=8, offset=5, type=MessageEntityType.MENTION),
                            MessageEntity(length=8, offset=5, type=MessageEntityType.BOLD),
                            MessageEntity(length=6, offset=13, type=MessageEntityType.BOLD),
                            MessageEntity(length=7, offset=19, type=MessageEntityType.BOLD),
                            MessageEntity(length=7, offset=19, type=MessageEntityType.ITALIC),
                            MessageEntity(length=7, offset=26, type=MessageEntityType.HASHTAG),
                            MessageEntity(length=7, offset=26, type=MessageEntityType.BOLD),
                            MessageEntity(length=7, offset=26, type=MessageEntityType.ITALIC),
                            MessageEntity(length=5, offset=33, type=MessageEntityType.BOLD),
                            MessageEntity(length=11, offset=38, type=MessageEntityType.BOLD),
                            MessageEntity(length=11, offset=38, type=MessageEntityType.UNDERLINE),
                            MessageEntity(length=17, offset=49, type=MessageEntityType.EMAIL),
                            MessageEntity(length=17, offset=49, type=MessageEntityType.BOLD),
                            MessageEntity(length=17, offset=49, type=MessageEntityType.UNDERLINE))

    def test_simple_entities_inside_blockquote(self):
        test_text = ("<blockquote>Some text with @mention #hashtag $CASH "
                "/command email@example.com +18001234567</blockquote>")

        text, entities = self.sut(test_text, ParseMode.HTML)

        assert text == "Some text with @mention #hashtag $CASH /command email@example.com +18001234567"
        assert entities == (MessageEntity(length=78, offset=0, type=MessageEntityType.BLOCKQUOTE),
                            MessageEntity(length=8, offset=15, type=MessageEntityType.MENTION),
                            MessageEntity(length=8, offset=24, type=MessageEntityType.HASHTAG),
                            MessageEntity(length=5, offset=33, type=MessageEntityType.CASHTAG),
                            MessageEntity(length=8, offset=39, type=MessageEntityType.BOT_COMMAND),
                            MessageEntity(length=17, offset=48, type=MessageEntityType.EMAIL),
                            MessageEntity(length=12, offset=66, type=MessageEntityType.PHONE_NUMBER))

    def test_simple_entities_inside_code(self):
        test_text = ("<code>Some text with @mention #hashtag $CASH "
                     "/command email@example.com +18001234567</code>")

        text, entities = self.sut(test_text, ParseMode.HTML)

        assert text == "Some text with @mention #hashtag $CASH /command email@example.com +18001234567"
        assert entities == (MessageEntity(length=78, offset=0, type=MessageEntityType.CODE),)

    def test_simple_entities_inside_pre(self):
        test_text = ("<pre class='language-pythoh'>@mention #hashtag "
                "$CASH /command email@example.com +18001234567</pre>")

        text, entities = self.sut(test_text, "HTML")

        assert text == "@mention #hashtag $CASH /command email@example.com +18001234567"
        assert entities == (MessageEntity(length=63, offset=0, type=MessageEntityType.PRE),)

    def test_simple_entities_inside_url(self):
        test_text = ("<a href='https://example.com'>@mention #hashtag "
                     "$CASH /command email@example.com +18001234567</a>")

        text, entities = self.sut(test_text, "HTML")

        assert text == "@mention #hashtag $CASH /command email@example.com +18001234567"
        assert entities == (MessageEntity(length=63, offset=0,
                                          type=MessageEntityType.TEXT_LINK,
                                          url="https://example.com/"),)

    def test_valid_mention_inside_tag_url(self):
        test_text = "<a>https://@@example.com</a>"
        text, entities = self.sut(test_text, "HTML")

        assert text == "https://@@example.com"
        assert entities == (MessageEntity(length=8, offset=9,
                                          type=MessageEntityType.MENTION),)

    def test_valid_mention_inside_plain_url(self):
        assert self.sut("https://@example.com", None) == ("https://@example.com",
                                                                        (MessageEntity(length=8, offset=8,
                                                                                       type=MessageEntityType.MENTION),))
        assert self.sut("go @ogle.com", None) == ("go @ogle.com",
                                                                (MessageEntity(length=5, offset=3,
                                                                               type=MessageEntityType.MENTION),))

    def test_invalid_mention_inside_plain_url(self):
        assert self.sut("go@ogle.com", None) == ("go@ogle.com",
                                                                (MessageEntity(length=11, offset=0,
                                                                               type=MessageEntityType.EMAIL),))

        assert self.sut("go-@ogle.com", None) == ("go-@ogle.com",
                                                                (MessageEntity(length=12, offset=0,
                                                                               type=MessageEntityType.EMAIL),))

        assert self.sut("https://google.com/@command", None) == ("https://google.com/@command",
                                                                                (MessageEntity(length=27, offset=0,
                                                                                               type=MessageEntityType.URL),))

    def test_url_with_basic_auth(self):
        assert self.sut("https://user:path@google.com", None) == ("https://user:path@google.com",
                                                                              (MessageEntity(length=28, offset=0,
                                                                                             type=MessageEntityType.URL),))
        assert self.sut("http://a@google.com", None) == ("http://a@google.com",
                                                                     (MessageEntity(length=19, offset=0,
                                                                                    type=MessageEntityType.URL),))
        assert self.sut("http://test@google.com", None) == ("http://test@google.com",
                                                                        (MessageEntity(length=22, offset=0,
                                                                                       type=MessageEntityType.URL),))

    def test_valid_hashtag_inside_plain_url(self):
        assert self.sut("https://#example.com", None) == ("https://#example.com",
                                                                      (MessageEntity(length=8, offset=8,
                                                                                     type=MessageEntityType.HASHTAG),))
        assert self.sut("go #ogle.com", None) == ("go #ogle.com", (
                                                                MessageEntity(length=5, offset=3,
                                                                              type=MessageEntityType.HASHTAG),))
        assert self.sut("#example.com/#hash", None) == ("#example.com/#hash", (MessageEntity(length=8, offset=0, type=MessageEntityType.HASHTAG),
                                                                               MessageEntity(length=5, offset=13, type=MessageEntityType.HASHTAG)))

    def test_invalid_hashtag_inside_plain_url(self):
        assert self.sut("go#ogle.com", None) == ("go#ogle.com",
                                                                (MessageEntity(length=8, offset=3,
                                                                               type=MessageEntityType.URL),))
        assert self.sut("http://google.com/#hash", None) == ("http://google.com/#hash",
                                                                            (MessageEntity(length=23, offset=0,
                                                                                           type=MessageEntityType.URL),))

    def test_valid_cashtag_inside_plain_url(self):
        test_text = "https://$EXAMPLE.com"

        text, entities = self.sut(test_text, None)

        assert text == test_text
        assert entities == (MessageEntity(length=8, offset=8, type=MessageEntityType.CASHTAG),)

    def test_valid_bot_command_inside_plain_url(self):
        assert self.sut("http:/google.com/command", None) == ("http:/google.com/command",
                                                                            (MessageEntity(length=7,
                                                                                           offset=5,
                                                                                           type=MessageEntityType.BOT_COMMAND),))

    def test_invalid_bot_command_inside_plain_url(self):
        assert self.sut("https://example/command.com", None) == ("https://example/command.com",
                                                                                (MessageEntity(length=11,
                                                                                               offset=16,
                                                                                               type=MessageEntityType.URL),))
        assert self.sut("http://google.com/command", None) == ("http://google.com/command",
                                                                            (MessageEntity(length=25,
                                                                                           offset=0,
                                                                                           type=MessageEntityType.URL),))
        assert self.sut("//google.com/command", None) == ("//google.com/command",
                                                                        (MessageEntity(length=18,
                                                                                       offset=2,
                                                                                       type=MessageEntityType.URL),))

    @pytest.mark.parametrize(["tag"], (("b", ), ("strong", ), ("i", ), ("em", ),
                                       ("s", ), ("strike", ), ("del", ), ("u", ),
                                       ("ins", ), ("tg-spoiler", )))
    def test_markup_entity_intersects_inline_url(self, tag):
        test_text = f"<{tag}>https://goo</{tag}>gle.com"

        text, entities = self.sut(test_text, ParseMode.HTML)

        assert text == "https://google.com"
        assert entities == (MessageEntity(length=18, offset=0, type=MessageEntityType.URL),
                            MessageEntity(length=11, offset=0, type=self.entities[tag]))

    def test_email(self):
        text, entities = self.sut("email@example.com", None)

        assert text == "email@example.com"
        assert entities == (MessageEntity(length=17, offset=0,
                                          type=MessageEntityType.EMAIL),)

    def test_urls(self):
        assert self.sut("tg://test:asd@google.com:80", None) ==  ('tg://test:asd@google.com:80',
                                                                              (MessageEntity(length=9, offset=0,
                                                                                             type=MessageEntityType.URL),))

    def test_complex(self):
        test_text = ("a.b.google.com dfsknnfs gsdfgsg http://códuia.de/ dffdg,\" "
                     "12)(cpia.de/())(\" http://гришка.рф/ sdufhdf "
                     "http://xn--80afpi2a3c.xn--p1ai/ I have a good time.Thanks, guys!\n\n"
                     "(hdfughidufhgdis) go#ogle.com гришка.рф hsighsdf gi почта.рф\n\n"
                     "✪df.ws/123      xn--80afpi2a3c.xn--p1ai\n\nhttp://foo.com/blah_blah\n"
                     "http://foo.com/blah_blah/\n(Something like http://foo.com/blah_blah)\n"
                     "http://foo.com/blah_blah_(wikipedi8989a_Вася)\n(Something like "
                     "http://foo.com/blah_blah_(Стакан_007))\nhttp://foo.com/blah_blah.\n"
                     "http://foo.com/blah_blah/.\n<http://foo.com/"
                     "blah_blah>\n<http://fo@@@@@@@@@^%#*@^&@$#*@#%^*&!^#o.com/blah_blah/>\n"
                     "http://foo.com/blah_blah,\nhttp://www.example.com/wpstyle/?p=364.\n"
                     "http://✪df.ws/123\nrdar://1234\nrdar:/1234\nhttp://"
                     "userid:password@example.com:8080\nhttp://userid@example.com\n"
                     "http://userid@example.com:8080\nhttp://userid:password@example.com\n"
                     "http://example.com:8080 x-yojimbo-item://6303E4C1-xxxx-45A6-AB9D-3A908F59AE0E\n"
                     "message://%3c330e7f8409726r6a4ba78dkf1fd71420c1bf6ff@mail.gmail.com%3e\n"
                     "\n<tag>http://example.com</tag>\nJust a www.example.com "
                     "link.\n\nabcdefghijklmnopqrstuvwxyz0123456789qwe_sdfsdf.aweawe-sdfs.com\n"
                     "google.com:᪉᪉᪉᪉\ngoogle.com:᪀᪀\nhttp://  .com\nURL:     .com\nURL: "  # noqa: RUF001
                     ".com\n\ngoogle.com?qwe\ngoogle.com#qwe\ngoogle.com/?\ngoogle.com/#\n"
                     "google.com?\ngoogle.com#\n")

        text, entities = self.sut(test_text, None)
        assert text == test_text.strip()
        assert entities == (MessageEntity(length=14, offset=0, type=MessageEntityType.URL),
                            MessageEntity(length=17, offset=32, type=MessageEntityType.URL),
                            MessageEntity(length=10, offset=62, type=MessageEntityType.URL),
                            MessageEntity(length=17, offset=76, type=MessageEntityType.URL),
                            MessageEntity(length=31, offset=102, type=MessageEntityType.URL),
                            MessageEntity(length=8, offset=189, type=MessageEntityType.URL),
                            MessageEntity(length=9, offset=198, type=MessageEntityType.URL),
                            MessageEntity(length=8, offset=220, type=MessageEntityType.URL),
                            MessageEntity(length=10, offset=230, type=MessageEntityType.URL),
                            MessageEntity(length=23, offset=246, type=MessageEntityType.URL),
                            MessageEntity(length=24, offset=271, type=MessageEntityType.URL),
                            MessageEntity(length=25, offset=296, type=MessageEntityType.URL),
                            MessageEntity(length=24, offset=338, type=MessageEntityType.URL),
                            MessageEntity(length=45, offset=364, type=MessageEntityType.URL),
                            MessageEntity(length=37, offset=426, type=MessageEntityType.URL),
                            MessageEntity(length=24, offset=465, type=MessageEntityType.URL),
                            MessageEntity(length=25, offset=491, type=MessageEntityType.URL),
                            MessageEntity(length=24, offset=519, type=MessageEntityType.URL),
                            MessageEntity(length=2, offset=583, type=MessageEntityType.HASHTAG),
                            MessageEntity(length=24, offset=602, type=MessageEntityType.URL),
                            MessageEntity(length=37, offset=628, type=MessageEntityType.URL),
                            MessageEntity(length=17, offset=667, type=MessageEntityType.URL),
                            MessageEntity(length=5, offset=702, type=MessageEntityType.BOT_COMMAND),
                            MessageEntity(length=39, offset=708, type=MessageEntityType.URL),
                            MessageEntity(length=25, offset=748, type=MessageEntityType.URL),
                            MessageEntity(length=30, offset=774, type=MessageEntityType.URL),
                            MessageEntity(length=34, offset=805, type=MessageEntityType.URL),
                            MessageEntity(length=23, offset=840, type=MessageEntityType.URL),
                            MessageEntity(length=18, offset=995, type=MessageEntityType.URL),
                            MessageEntity(length=15, offset=1027, type=MessageEntityType.URL),
                            MessageEntity(length=62, offset=1050, type=MessageEntityType.URL),
                            MessageEntity(length=10, offset=1113, type=MessageEntityType.URL),
                            MessageEntity(length=10, offset=1129, type=MessageEntityType.URL),
                            MessageEntity(length=14, offset=1182, type=MessageEntityType.URL),
                            MessageEntity(length=14, offset=1197, type=MessageEntityType.URL),
                            MessageEntity(length=11, offset=1212, type=MessageEntityType.URL),
                            MessageEntity(length=12, offset=1225, type=MessageEntityType.URL),
                            MessageEntity(length=10, offset=1238, type=MessageEntityType.URL),
                            MessageEntity(length=10, offset=1250, type=MessageEntityType.URL))

    def test_all_entities_with_markup(self):
        test_text = ("  <i><b>Lorem</b> <s>ipsum</s> dolor sit amet</i>,"
                     " <em>consectetur <strong>adipiscing</strong> elit</em>. "
                     "<strike>Sed @ultricies #vulputate $PORTA</strike>. "
                     "<del>Curabitur /tellus dui</del>, <u>blandit ut pharetra a</u>, "
                     "<tg-spoiler><ins>accumsan vitae massa +1(800)1234567</ins></tg-spoiler>. "
                     "<code>Nunc @diam #ante, /pellentesque $QUIS ante@example.com +18001234567</code> "
                     "fringilla@email.com, https://mattis.com sollicitudin.net sem. "
                     "<a>@Orci varius,</a> "
                     "<a href='http://google.com'>@natoque #penatibus et /magnis $DIS</a> "
                     "parturient montes, nascetur ridiculus mus. "
                     "<blockquote>@Nulla /vel #quam at $LECTUS tempus@elemen.tum +18001234567.</blockquote>  "
                     "Etiam tg://resolve?domain=imperdiet vitae tortor a rhoncus.  "
                     "<blockquote expandable>Nullam mollis sollicitudin placerat.\n"
                     "Nam porttitor justo quis dolor porta tristique.\n"
                     "Donec rhoncus semper mollis.\n"
                     "Sed ac porta elit, vitae aliquam sapien.\n"
                     "In /hac @habitasse #platea dictumst.\n"
                     "Proin viverra $LACUS magna,\n"
                     "in lobortis sem fringilla sit amet. \n\n</blockquote>")

        text, entities = self.sut(test_text, "HTML")

        assert text == ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                        "Sed @ultricies #vulputate $PORTA. Curabitur /tellus dui, "
                        "blandit ut pharetra a, accumsan vitae massa +1(800)1234567. "
                        "Nunc @diam #ante, /pellentesque $QUIS ante@example.com +18001234567 "
                        "fringilla@email.com, https://mattis.com sollicitudin.net sem. "
                        "@Orci varius, @natoque #penatibus et /magnis $DIS parturient montes, "
                        "nascetur ridiculus mus. @Nulla /vel #quam at $LECTUS tempus@elemen.tum "
                        "+18001234567.  Etiam tg://resolve?domain=imperdiet vitae tortor a rhoncus.  "
                        "Nullam mollis sollicitudin placerat.\n"
                        "Nam porttitor justo quis dolor porta tristique.\n"
                        "Donec rhoncus semper mollis.\n"
                        "Sed ac porta elit, vitae aliquam sapien.\n"
                        "In /hac @habitasse #platea dictumst.\n"
                        "Proin viverra $LACUS magna,\n"
                        "in lobortis sem fringilla sit amet.")

        assert entities == (MessageEntity(length=6, offset=0, type=MessageEntityType.ITALIC),
                            MessageEntity(length=5, offset=0, type=MessageEntityType.BOLD),
                            MessageEntity(length=20, offset=6, type=MessageEntityType.ITALIC),
                            MessageEntity(length=5, offset=6, type=MessageEntityType.STRIKETHROUGH),
                            MessageEntity(length=12, offset=28, type=MessageEntityType.ITALIC),
                            MessageEntity(length=15, offset=40, type=MessageEntityType.ITALIC),
                            MessageEntity(length=10, offset=40, type=MessageEntityType.BOLD),
                            MessageEntity(length=4, offset=57, type=MessageEntityType.STRIKETHROUGH),
                            MessageEntity(length=10, offset=61, type=MessageEntityType.MENTION),
                            MessageEntity(length=10, offset=61, type=MessageEntityType.STRIKETHROUGH),
                            MessageEntity(length=1, offset=71, type=MessageEntityType.STRIKETHROUGH),
                            MessageEntity(length=10, offset=72, type=MessageEntityType.HASHTAG),
                            MessageEntity(length=10, offset=72, type=MessageEntityType.STRIKETHROUGH),
                            MessageEntity(length=1, offset=82, type=MessageEntityType.STRIKETHROUGH),
                            MessageEntity(length=6, offset=83, type=MessageEntityType.CASHTAG),
                            MessageEntity(length=6, offset=83, type=MessageEntityType.STRIKETHROUGH),
                            MessageEntity(length=10, offset=91, type=MessageEntityType.STRIKETHROUGH),
                            MessageEntity(length=7, offset=101, type=MessageEntityType.BOT_COMMAND),
                            MessageEntity(length=7, offset=101, type=MessageEntityType.STRIKETHROUGH),
                            MessageEntity(length=4, offset=108, type=MessageEntityType.STRIKETHROUGH),
                            MessageEntity(length=21, offset=114, type=MessageEntityType.UNDERLINE),
                            MessageEntity(length=21, offset=137, type=MessageEntityType.UNDERLINE),
                            MessageEntity(length=21, offset=137, type=MessageEntityType.SPOILER),
                            MessageEntity(length=14, offset=158, type=MessageEntityType.PHONE_NUMBER),
                            MessageEntity(length=14, offset=158, type=MessageEntityType.UNDERLINE),
                            MessageEntity(length=14, offset=158, type=MessageEntityType.SPOILER),
                            MessageEntity(length=67, offset=174, type=MessageEntityType.CODE),
                            MessageEntity(length=19, offset=242, type=MessageEntityType.EMAIL),
                            MessageEntity(length=18, offset=263, type=MessageEntityType.URL),
                            MessageEntity(length=16, offset=282, type=MessageEntityType.URL),
                            MessageEntity(length=5, offset=304, type=MessageEntityType.MENTION),
                            MessageEntity(length=35, offset=318, type=MessageEntityType.TEXT_LINK,
                                          url="http://google.com/"),
                            MessageEntity(length=60, offset=397, type=MessageEntityType.BLOCKQUOTE),
                            MessageEntity(length=6, offset=397, type=MessageEntityType.MENTION),
                            MessageEntity(length=4, offset=404, type=MessageEntityType.BOT_COMMAND),
                            MessageEntity(length=5, offset=409, type=MessageEntityType.HASHTAG),
                            MessageEntity(length=7, offset=418, type=MessageEntityType.CASHTAG),
                            MessageEntity(length=17, offset=426, type=MessageEntityType.EMAIL),
                            MessageEntity(length=12, offset=444, type=MessageEntityType.PHONE_NUMBER),
                            MessageEntity(length=29, offset=465, type=MessageEntityType.URL),
                            MessageEntity(length=255, offset=520, type=MessageEntityType.EXPANDABLE_BLOCKQUOTE),
                            MessageEntity(length=4, offset=678, type=MessageEntityType.BOT_COMMAND),
                            MessageEntity(length=10, offset=683, type=MessageEntityType.MENTION),
                            MessageEntity(length=7, offset=694, type=MessageEntityType.HASHTAG),
                            MessageEntity(length=6, offset=726, type=MessageEntityType.CASHTAG))

    def test_empty_string(self):
        with pytest.raises(BadMarkupException, match="Message text is empty"):
            self.sut("", None)

    def test_whitespaces_only(self):
        with pytest.raises(BadMarkupException, match="Text must be non-empty"):
            self.sut("      ", None)

    def test_empty_entity(self):
        with pytest.raises(BadMarkupException, match="Text must be non-empty"):
            self.sut("<a></a>", "HTML")

    def test_nested_entities(self):
        assert self.sut("<i><b>@mention</b> </i>text",
                        "HTML") == ("@mention text",
                                           (MessageEntity(length=8, offset=0, type=MessageEntityType.MENTION),
                                            MessageEntity(length=8, offset=0, type=MessageEntityType.BOLD),
                                            MessageEntity(length=8, offset=0, type=MessageEntityType.ITALIC),
                                            MessageEntity(length=1, offset=8, type=MessageEntityType.ITALIC)))

        assert self.sut("<b>@mention <i>#hashtag</i> $ABC</b>",
                        "HTML") == (("@mention #hashtag $ABC",
                                            (MessageEntity(length=8, offset=0, type=MessageEntityType.MENTION),
                                             MessageEntity(length=8, offset=0, type=MessageEntityType.BOLD),
                                             MessageEntity(length=1, offset=8, type=MessageEntityType.BOLD),
                                             MessageEntity(length=8, offset=9, type=MessageEntityType.HASHTAG),
                                             MessageEntity(length=8, offset=9, type=MessageEntityType.BOLD),
                                             MessageEntity(length=8, offset=9, type=MessageEntityType.ITALIC),
                                             MessageEntity(length=1, offset=17, type=MessageEntityType.BOLD),
                                             MessageEntity(length=4, offset=18, type=MessageEntityType.CASHTAG),
                                             MessageEntity(length=4, offset=18, type=MessageEntityType.BOLD))))

    def test_misc(self):
        assert self.sut("@views.py'", None) == ("@views.py'",
                                                            (MessageEntity(length=6, offset=0,
                                                                           type=MessageEntityType.MENTION),))
        assert self.sut("a:b?@gmail.com", None) == ("a:b?@gmail.com",
                                                                (MessageEntity(length=6, offset=4,
                                                                               type=MessageEntityType.MENTION),))
        assert self.sut("a:b#@gmail.com", None) == ("a:b#@gmail.com",
                                                                (MessageEntity(length=6, offset=4,
                                                                               type=MessageEntityType.MENTION),))
        assert self.sut("#views.py'", None) == ("#views.py'",
                                                            (MessageEntity(length=6, offset=0,
                                                                           type=MessageEntityType.HASHTAG),))
        assert self.sut("/views.py'", None) == ("/views.py'",
                                                            (MessageEntity(length=6, offset=0,
                                                                           type=MessageEntityType.BOT_COMMAND),))
        assert self.sut("a!:b@gmail.com", None) == ("a!:b@gmail.com",
                                                                (MessageEntity(length=14, offset=0,
                                                                               type=MessageEntityType.URL),))
        assert self.sut("https://google.com//command", None) == ("https://google.com//command",
                                                                 (MessageEntity(length=27, offset=0,
                                                                                type=MessageEntityType.URL),))
        assert self.sut("https://google.com/$ABC", None) == ("https://google.com/$ABC",
                                                             (MessageEntity(length=23, offset=0,
                                                                            type=MessageEntityType.URL),))
        assert self.sut("https://google.com/#hashtag", None) == ("https://google.com/#hashtag",
                                                                 (MessageEntity(length=27, offset=0,
                                                                                type=MessageEntityType.URL),))
