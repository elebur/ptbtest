from telegram import MessageEntity
from telegram.constants import MessageEntityType

from ptbtest.entityparser import EntityParser

class TestParseUrls:
    ep = EntityParser()

    def test_empty_string(self):
        assert self.ep.parse_urls("") == ()

    def test_no_urls_in_string(self):
        assert self.ep.parse_urls(".") == ()
        assert self.ep.parse_urls("Hello world.") == ()

    def test_invalid_urls(self):
        assert self.ep.parse_urls("http://  .com") == ()
        assert self.ep.parse_urls("URL:     .com") == ()
        assert self.ep.parse_urls("URL: .com") == ()
        assert self.ep.parse_urls(".com") == ()
        assert self.ep.parse_urls("http://  .") == ()
        assert self.ep.parse_urls("http://.") == ()
        assert self.ep.parse_urls("http://.com") == ()
        assert self.ep.parse_urls("http://  .") == ()
        assert self.ep.parse_urls("http://1.0") == ()
        assert self.ep.parse_urls("http://a.0") == ()
        assert self.ep.parse_urls("http://a.a") == ()
        assert self.ep.parse_urls("https://t.…") == ()

    def test_valid_domains(self):
        assert self.ep.parse_urls("telegram.org") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("(telegram.org)") == (MessageEntity(length=12, offset=1, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("\ntelegram.org)") == (MessageEntity(length=12, offset=1, type=MessageEntityType.URL),)
        assert self.ep.parse_urls(" telegram.org)") == (MessageEntity(length=12, offset=1, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("\"telegram.org\"") == (MessageEntity(length=12, offset=1, type=MessageEntityType.URL),)
        assert self.ep.parse_urls(" telegram.org ") == (MessageEntity(length=12, offset=1, type=MessageEntityType.URL),)
        assert self.ep.parse_urls(" telegram.org. ") == (MessageEntity(length=12, offset=1, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("google.com:᪉᪉᪉᪉᪉") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("telegram.ton") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("telegram.onion") == (MessageEntity(length=14, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("ТеСт.ОнЛайН") == (MessageEntity(length=11, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("ÀÁ.com. ÀÁ.com.") == (MessageEntity(length=6, offset=0, type=MessageEntityType.URL),
                                                         MessageEntity(length=6, offset=8, type=MessageEntityType.URL))
        assert self.ep.parse_urls("ÀÁ.com,ÀÁ.com.") == (MessageEntity(length=6, offset=0, type=MessageEntityType.URL),
                                                         MessageEntity(length=6, offset=7, type=MessageEntityType.URL))
        assert self.ep.parse_urls("https://a.de`bc") == (MessageEntity(length=15, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("telegram.ORG") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("_.test.com") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)

    def test_invalid_domains(self):
        assert self.ep.parse_urls(".telegram.org)") == ()
        assert self.ep.parse_urls("telegram.tonsite") == ()
        assert self.ep.parse_urls("a.ab") == ()
        assert self.ep.parse_urls("test.abd") == ()
        assert self.ep.parse_urls("ТеСт.Онлайн") == ()
        # The upper greek letter alpha.
        assert self.ep.parse_urls("ТеСт.ОнлΑЙН") == ()
        assert self.ep.parse_urls("ТеСт.Онлайнн") == ()
        assert self.ep.parse_urls("test.abd") == ()
        assert self.ep.parse_urls("telegram.Org") == ()
        assert self.ep.parse_urls("telegram.Org") == ()
        assert self.ep.parse_urls("a.b.c.com.a.b.c") == ()
        assert self.ep.parse_urls("http://test_.com") == ()
        assert self.ep.parse_urls("test_.com") == ()
        assert self.ep.parse_urls("_test.com") == ()
        assert self.ep.parse_urls("bad_domain.com") == ()

    def test_valid_protocols(self):
        assert self.ep.parse_urls("https://telegram.org") == (MessageEntity(length=20, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://telegram.org") == (MessageEntity(length=19, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("ftp://telegram.org") == (MessageEntity(length=18, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("tonsite://telegram.ton") == (MessageEntity(length=22, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://ÀТеСт.ОнЛайНн") == (MessageEntity(length=20, offset=0, type=MessageEntityType.URL),)

    def test_invalid_protocols(self):
        assert self.ep.parse_urls("sftp://telegram.org") == ()
        assert self.ep.parse_urls("ftps://telegram.org") == ()
        assert self.ep.parse_urls("invalid://telegram.org") == ()
        assert self.ep.parse_urls("sftp://telegram.org") == ()

    def test_without_protocol(self):
        assert self.ep.parse_urls("://telegram.org") == (MessageEntity(length=12, offset=3, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("telegram.org") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),)

    def test_slashes_without_protocol(self):
        assert self.ep.parse_urls("//telegram.org)") == (MessageEntity(length=12, offset=2, type=MessageEntityType.URL),)

    def test_comma_inside_url(self):
        assert self.ep.parse_urls("http://google,.com") == ()

    def test_with_params(self):
        assert self.ep.parse_urls("()telegram.org/?q=()") == (MessageEntity(length=18, offset=2, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://telegram.org/?asd=123#123.") == (MessageEntity(length=32, offset=0, type=MessageEntityType.URL),)

    def test_basic_auth_ignoring_mentions(self):
        """
        These tests will fail if they'll be testsed against the Telegram server,
        because mentions extracted before URLs and in this string http://@google.com
        "@google" as a mention will be found, and no URLs.
        """
        assert self.ep.parse_urls("http://@google.com") == (MessageEntity(length=10, offset=8, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://@goog.com") == (MessageEntity(length=8, offset=8, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://@@google.com") == (MessageEntity(length=10, offset=9, type=MessageEntityType.URL),)

    def test_basic_auth(self):
        assert self.ep.parse_urls("http://a@google.com") == (MessageEntity(length=19, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://test@google.com") ==  (MessageEntity(length=22, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://user:pass@google.com") ==  (MessageEntity(length=27, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://a:h.bcde.fg@c.com") == (MessageEntity(length=25, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://bc:defg@c.com") == (MessageEntity(length=21, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://a:hbc:defg@c.com") == (MessageEntity(length=24, offset=0, type=MessageEntityType.URL),)

    def test_uncommon_tld(self):
        # WITHOUT the protocol.
        assert self.ep.parse_urls("telegram.tonsite") == ()
        # WITH the protocol.
        assert self.ep.parse_urls("http://telegram.tonsite") == (MessageEntity(length=23, offset=0, type=MessageEntityType.URL),)

    def test_mix_cased_protocol(self):
        assert self.ep.parse_urls("hTtPs://telegram.org") == (MessageEntity(length=20, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("HTTP://telegram.org") == (MessageEntity(length=19, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://telegram.org") == (MessageEntity(length=20, offset=0, type=MessageEntityType.URL),)

    def test_protocols_with_leading_latin_char(self):
        assert self.ep.parse_urls("sHTTP://telegram.org") == ()
        assert self.ep.parse_urls(".ahttp://google.com") == ()

    def test_protocols_with_leading_non_latin_char(self):
        # The leading cyrillic letter 'a'.
        assert self.ep.parse_urls("аHTTP://telegram.org") == (MessageEntity(length=19, offset=1, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("൹HTTP://telegram.org") == (MessageEntity(length=19, offset=1, type=MessageEntityType.URL),)

    def test_very_long_url(self):
        assert self.ep.parse_urls("http://abcdefghijkabcdefghijkabcdefghijkabcdefg"
                                  "hijkabcdefghijkabcdefghijkabcdefghijkabcdefghij"
                                  "kabcdefghijkabcdefghijkabcdefghijkabcdefghijkab"
                                  "cdefghijkabcdefghijkabcdefghijkabcdefghijkabcde"
                                  "fghijkabcdefghijkabcdefghijkabcdefghijkabcdefgh"
                                  "ijkabcdefghijkabcdefghijkabcdefghijkabcdefghijk"
                                  "abcdefghijkabcdefghijkabcdefghijkabcdefghijkabc"
                                  "defghijkabcdefghijkabcdefghijkabcdefghijkabcdef"
                                  "ghijkabcdefghijkabcdefghijkabcdefghijkabcdefghi"
                                  "jkabcdefghijkabcdefghijkabcdefghijkabcdefghijka"
                                  "bcdefghijkabcdefghijkabcdefghijkabcdefghijkabcd"
                                  "efghijkabcdefghijkabcdefghijkabcdefghijkabcdefg"
                                  "hijkabcdefghijkabcdefghijkabcdefghijkabcdefghij"
                                  "kabcdefghijkabcdefghijkabcdefghijkabcdefghijkab"
                                  "cdefghijkabcdefghijkabcdefghijkabcdefghijkabcde"
                                  "fghijkabcdefghijkabcdefghijkabcdefghijkabcdefgh"
                                  "ijkabcdefghijkabcdefghijkabcdefghijkabcdefghijk"
                                  "abcdefghijkabcdefghijkabcdefghijkabcdefghijkabc"
                                  "defghijkabcdefghijkabcdefghijk.com") == ()

    def test_valid_ports(self):
        assert self.ep.parse_urls("google.com:1#ab c") == (MessageEntity(length=15, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("google.com:1#") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("google.com:1#1") == (MessageEntity(length=14, offset=0, type=MessageEntityType.URL),)
        # Leading zeros are acceptable (according to the Telegram rules).
        assert self.ep.parse_urls("google.com:00000001/abs") == (MessageEntity(length=23, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("google.com:000000065535/abs") == (MessageEntity(length=27, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("google.com:000000080/abs") == (MessageEntity(length=24, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("google.com:65535") == (MessageEntity(length=16, offset=0, type=MessageEntityType.URL),)

    def test_invalid_ports(self):
        # Too big port number (>65535)
        assert self.ep.parse_urls("google.com:000000065536/abs") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("google.com:65536") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("google.com:100000") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)
        # The port number overflow and invalid symbold in the path.
        assert self.ep.parse_urls("google.com:0000000655353/abs>>>>") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)
        # Zero port is not acceptable.
        assert self.ep.parse_urls("google.com:0000000/abs") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("google.com:0/abs") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)
        # Empty port.
        assert self.ep.parse_urls("google.com:/abs") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)

    def test_localhost_ip_address(self):
        assert self.ep.parse_urls("127.001") == ()
        assert self.ep.parse_urls("127.0.0.1") == (MessageEntity(length=9, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("127.0.0.01") == ()
        assert self.ep.parse_urls("127.0.0.256") == ()
        assert self.ep.parse_urls("127.0.0.300") == ()
        assert self.ep.parse_urls("127.0.0.260") == ()
        assert self.ep.parse_urls("1.0") == ()
        assert self.ep.parse_urls("127.0.0.1000") == ()

    def test_fake_domain_teiegram(self):
        assert self.ep.parse_urls("teiegram.org/test") == ()
        assert self.ep.parse_urls("TeiegraM.org/test") == ()
        assert self.ep.parse_urls("TeiegraM.org") == ()
        assert self.ep.parse_urls("teiegram.org") == ()

    def test_parentheses_and_brackets(self):
        assert self.ep.parse_urls("http://test.google.com/?q=abc()}[]def") == (MessageEntity(length=31, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://test.google.com/?q=abc([{)]}def") == (MessageEntity(length=38, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://test.google.com/?q=abc(){}]def") == (MessageEntity(length=33, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://test.google.com/?q=abc){}[]def") == (MessageEntity(length=29, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://test.google.com/?q=abc(){}[]def") == (MessageEntity(length=38, offset=0, type=MessageEntityType.URL),)

    def test_underscores(self):
        assert self.ep.parse_urls("http://google_.com") == ()
        assert self.ep.parse_urls("http://google._com_") == ()
        assert self.ep.parse_urls("http://test_.google.com") ==  (MessageEntity(length=23, offset=0, type=MessageEntityType.URL),)

    def test_hyphen_at_end_of_domain_and_subdomain(self):
        assert self.ep.parse_urls("http://test-.google.com") == ()
        assert self.ep.parse_urls("http://test.google-.com") == ()

    def test_ipv6_address(self):
        assert self.ep.parse_urls("http://[2001:4860:0:2001::68]/") == ()

    def test_tg_domains(self):
        assert self.ep.parse_urls("tg://resolve") == ()

    def test_different_url_endings(self):
        assert self.ep.parse_urls("http://google.com/") == (MessageEntity(length=18, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://google.com?") == (MessageEntity(length=17, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://google.com#") == (MessageEntity(length=17, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://google.com##") == (MessageEntity(length=19, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://google.com/?") == (MessageEntity(length=18, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://www.google.com/ab,") == (MessageEntity(length=25, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://test.com#a") == (MessageEntity(length=17, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://test.com#") == (MessageEntity(length=15, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://test.com?#") == (MessageEntity(length=17, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://test.com/?#") == (MessageEntity(length=18, offset=0, type=MessageEntityType.URL),)

    def test_at_symbol(self):
        assert self.ep.parse_urls("https://a.bc@c.com") == (MessageEntity(length=18, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://a.de/bc@c.com") == (MessageEntity(length=21, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://a.debc@c.com") == (MessageEntity(length=20, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://a.de`bc@c.com") == (MessageEntity(length=15, offset=0, type=MessageEntityType.URL),
                                                               MessageEntity(length=5, offset=16, type=MessageEntityType.URL))

        assert self.ep.parse_urls("https://a.bcde.fg@c.com") == (MessageEntity(length=23, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://abc@c.com") == (MessageEntity(length=17, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://a.bc@test.com:cd.com") == (MessageEntity(length=21, offset=0, type=MessageEntityType.URL),
                                                                      MessageEntity(length=6, offset=22, type=MessageEntityType.URL))

    def test_filenames_like_urls(self):
        assert self.ep.parse_urls("File '/usr/views.py'") == (MessageEntity(length=8, offset=11, type=MessageEntityType.URL),)
        assert self.ep.parse_urls(".views.py") == ()
        assert self.ep.parse_urls("'views.py'") == (MessageEntity(length=8, offset=1, type=MessageEntityType.URL),)

    def test_misc(self):
        assert self.ep.parse_urls("telegram. org. www. com... telegram.org... ...google.com...") == (MessageEntity(length=12, offset=27, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("Такой сайт: http://www.google.com или такой telegram.org") == (MessageEntity(length=21, offset=12, type=MessageEntityType.URL),
                                                                                                  MessageEntity(length=12, offset=44, type=MessageEntityType.URL))
        assert self.ep.parse_urls("[http://google.com](test)") == (MessageEntity(length=17, offset=1, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("google.com:᪀᪀") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("/.b/..a    @.....@/. a.ba") == (MessageEntity(length=4, offset=21, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("('http://telegram.org/a-b/?br=ie&lang=en',)") == (MessageEntity(length=38, offset=2, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://ai.telegram.org/bot%20bot/test-...") == (MessageEntity(length=39, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("bbbbbbbbbbbbbb.@.@") == ()
        assert self.ep.parse_urls("@.") == ()
        assert self.ep.parse_urls("<http://www.ics.uci.edu/pub/ietf/uri/historical.html#WARNING>") == (MessageEntity(length=59, offset=1, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://t.me/abcdef…") == (MessageEntity(length=19, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://t.me…") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://t.m…") == ()
        assert self.ep.parse_urls("https://t.…") == ()
        assert self.ep.parse_urls("https://t…") == ()
        assert self.ep.parse_urls(".?") == ()
        assert self.ep.parse_urls("👉http://ab.com/cdefgh-1IJ") == (MessageEntity(length=24, offset=2, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("http://test―‑@―google―.―com―/―–―‐―/―/―/―?―‑―#―――") == (MessageEntity(length=48, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("a!:b@gmail.com") == (MessageEntity(length=14, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("a:b!@gmail.com") == (MessageEntity(length=14, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("_sip._udp.apnic.net") == (MessageEntity(length=19, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_urls("https://as_sip._udp.apnic.net") == (MessageEntity(length=29, offset=0, type=MessageEntityType.URL),)

    def test_emails(self):
        assert self.ep.parse_urls("a.bc@c.com") == (MessageEntity(length=10, offset=0, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("https://a.de[bc@c.com") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),
                                                               MessageEntity(length=8, offset=13, type=MessageEntityType.EMAIL))
        assert self.ep.parse_urls("https://a.de]bc@c.com") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),
                                                               MessageEntity(length=8, offset=13, type=MessageEntityType.EMAIL))
        assert self.ep.parse_urls("https://a.de{bc@c.com") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),
                                                               MessageEntity(length=8, offset=13, type=MessageEntityType.EMAIL))
        assert self.ep.parse_urls("https://a.de}bc@c.com") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),
                                                               MessageEntity(length=8, offset=13, type=MessageEntityType.EMAIL))
        assert self.ep.parse_urls("https://a.de(bc@c.com") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),
                                                               MessageEntity(length=8, offset=13, type=MessageEntityType.EMAIL))
        assert self.ep.parse_urls("https://a.de)bc@c.com") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),
                                                               MessageEntity(length=8, offset=13, type=MessageEntityType.EMAIL))
        assert self.ep.parse_urls("https://a.de'bc@c.com") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),
                                                               MessageEntity(length=8, offset=13, type=MessageEntityType.EMAIL))
        assert self.ep.parse_urls("https://de[bc@c.com") == (MessageEntity(length=8, offset=11, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("https://de/bc@c.com") == (MessageEntity(length=8, offset=11, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("https://de[bc@c.com") == (MessageEntity(length=8, offset=11, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("https://de{bc@c.com") == (MessageEntity(length=8, offset=11, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("https://de}bc@c.com") == (MessageEntity(length=8, offset=11, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("https://de(bc@c.com") == (MessageEntity(length=8, offset=11, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("https://de)bc@c.com") == (MessageEntity(length=8, offset=11, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("https://de\\bc@c.com") == (MessageEntity(length=8, offset=11, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("https://de'bc@c.com") == (MessageEntity(length=8, offset=11, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("https://de`bc@c.com") == (MessageEntity(length=8, offset=11, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("a@b@c.com") == (MessageEntity(length=7, offset=2, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("a@b.com:c@1") == (MessageEntity(length=7, offset=0, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("test@test.software") == (MessageEntity(length=18, offset=0, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("abc@c.com@d.com") == (MessageEntity(length=9, offset=0, type=MessageEntityType.EMAIL),
                                                         MessageEntity(length=5, offset=10, type=MessageEntityType.URL))
        assert self.ep.parse_urls("Look :test@example.com") == (MessageEntity(length=16, offset=6, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("a#:b@gmail.com") == (MessageEntity(length=11, offset=3, type=MessageEntityType.EMAIL),)
        assert self.ep.parse_urls("Look mailto:test@example.com") == (MessageEntity(length=16, offset=12, type=MessageEntityType.EMAIL),)
