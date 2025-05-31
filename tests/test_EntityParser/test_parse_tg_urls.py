import pytest
from telegram import MessageEntity
from telegram.constants import MessageEntityType

from ptbtest.entityparser import EntityParser

class TestParseTgUrls:
    ep = EntityParser()

    def test_empty_string(self):
        assert self.ep.parse_tg_urls("") == ()

    def test_string_without_url(self):
        assert self.ep.parse_tg_urls("abcd") == ()

    def test_valid_protocols(self):
        assert self.ep.parse_tg_urls("tg://resolve?domain=test_ch") == (MessageEntity(length=27, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("ton://EQCD39VS5jXptHL8vMjERrzGaRcCVYto8HUn4bpAog8xAB2N/transfer?amount=1&text=hello") == (MessageEntity(length=83, offset=0, type=MessageEntityType.URL),)
        # tonsite:// will be processed by the `parse_urls_and_emails` method.

    @pytest.mark.parametrize(["protocol"], (("http", ), ("ftp", ), ("ws", )))
    def test_invalid_protocols(self, protocol):
        assert self.ep.parse_tg_urls(f"{protocol}://resolve?domain=test_ch") == ()

    def test_protocol_only(self):
        assert self.ep.parse_tg_urls("tg://") == ()
        assert self.ep.parse_tg_urls("ton://") == ()

    def test_valid_urls_without_path(self):
        assert self.ep.parse_tg_urls("tg://a") == (MessageEntity(length=6, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://test/") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://test?asdf") == (MessageEntity(length=14, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://test#asdf") == (MessageEntity(length=14, offset=0, type=MessageEntityType.URL),)

    def test_valid_urls_with_path(self):
        assert self.ep.parse_tg_urls("tg://test/―asd―?asd=asd&asdas=―#――――") == (MessageEntity(length=36,
                                                                                               offset=0,
                                                                                               type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://test/?asd") == (MessageEntity(length=14, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://test/#asdf") == (MessageEntity(length=15, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://resolve?domain=username") == (MessageEntity(length=28, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://resolve?domain=somechannel&post=1234") == (MessageEntity(length=41, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://join?invite=CxZg5go3c6rlWAjcvOYI") == (MessageEntity(length=37, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://msg_url?url=example.com&text=sometexthere") == (MessageEntity(length=46, offset=0, type=MessageEntityType.URL),)

    def test_bad_path_end_chars(self):
        assert self.ep.parse_tg_urls("tg://test?.:;,(\"?!`.:;,(\"?!`") == (MessageEntity(length=9, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://test/?.:;,(\"?!`.:;,(\"?!`") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://test/?.:;,(\"?!`.:;,(\"?!`text") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)

    def test_embed_url(self):
        assert self.ep.parse_tg_urls("stg://a") == (MessageEntity(length=6, offset=1, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("asd  asdas das ton:asd tg:test "
                                     "ton://resolve tg://resolve "
                                     "TON://_-RESOLVE_- TG://-_RESOLVE-_") == (MessageEntity(length=13, offset=31, type=MessageEntityType.URL),
                                                                               MessageEntity(length=12, offset=45, type=MessageEntityType.URL),
                                                                               MessageEntity(length=17, offset=58, type=MessageEntityType.URL),
                                                                               MessageEntity(length=16, offset=76, type=MessageEntityType.URL))

    def test_invalid_urls(self):
        assert self.ep.parse_tg_urls("tg:test/") == ()
        assert self.ep.parse_tg_urls("tg:/test/") == ()
        assert self.ep.parse_tg_urls("tg://%30/sccct") == ()
        assert self.ep.parse_tg_urls("tg://б.а.н.а.на") == ()  # noqa: RUF001

    def test_hash_sign_and_question_mark_at_the_end(self):
        assert self.ep.parse_tg_urls("tg://test/?") == (MessageEntity(length=10, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://test/#") == (MessageEntity(length=11, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://test?") == (MessageEntity(length=9, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://test#") == (MessageEntity(length=9, offset=0, type=MessageEntityType.URL),)

    @pytest.mark.parametrize(["char"], "‖<>\"«»")
    def test_bad_chars_in_url(self, char):
        assert self.ep.parse_tg_urls(f"tg://test?as{char}df") == (MessageEntity(length=12, offset=0, type=MessageEntityType.URL),)

    @pytest.mark.parametrize(["char"], "()[]{'}$%")
    def test_valid_urls_with_special_symbol(self, char):
        assert self.ep.parse_tg_urls(f"tg://test?as{char}df") == (MessageEntity(length=15, offset=0, type=MessageEntityType.URL),)

    def test_misc(self):
        assert self.ep.parse_tg_urls("tg://test:asd@google.com:80") == (MessageEntity(length=9, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://google.com") == (MessageEntity(length=11, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://google/.com") == (MessageEntity(length=16, offset=0, type=MessageEntityType.URL),)
        assert self.ep.parse_tg_urls("tg://127.0.0.1") == (MessageEntity(length=8, offset=0, type=MessageEntityType.URL),)

    @pytest.mark.parametrize(["url"], (("TG://test", ), ("tG://TeSt", ), ("TG://TEST", )))
    def test_mixed_case(self, url):
        assert self.ep.parse_tg_urls(url) == (MessageEntity(length=9, offset=0, type=MessageEntityType.URL),)
