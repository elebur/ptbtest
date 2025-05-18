from telegram import MessageEntity
from telegram.constants import MessageEntityType

from ptbtest.entityparser import (_get_utf16_length,
                                  get_item,
                                  _check_and_normalize_url,
                                  _split_and_sort_intersected_entities)


def test_get_utf16_length():
    assert _get_utf16_length("a") == 1  # ASCII
    assert _get_utf16_length("hello") == 5  # Multiple ASCII symbols
    assert _get_utf16_length("€") == 1  # Euro (part of the BPM)
    assert _get_utf16_length("𐍈") == 2  # UTF-16 surrogate pair
    assert _get_utf16_length("👨‍👩‍👧‍👦") == 11 # Emoji with ZWJ (Zero Width Joiner)
    assert _get_utf16_length("") == 0  # Empty string
    assert _get_utf16_length("👀🔥") == 4  # Two emojis (each has 2 UTF-16 units)


class TestGetItem:
    seq = [10, 20, 40, 50, 60]

    def test_good_positive_indexes(self):
        assert get_item(self.seq, 0) == 10
        assert get_item(self.seq, 2) == 40
        assert get_item(self.seq, 4) == 60

    def test_good_negative_indexes(self):
        assert get_item(self.seq, -1) == 60
        assert get_item(self.seq, -3) == 40
        assert get_item(self.seq, -5) == 10

    def test_positive_indexes_out_of_range(self):
        assert get_item(self.seq, 5) is None
        assert get_item(self.seq, 10, "default") == "default"
        assert get_item(self.seq, 6, 0) == 0

    def test_negative_indexes_out_of_range(self):
        assert get_item(self.seq, -6) is None
        assert get_item(self.seq, -10, "default") == "default"
        assert get_item(self.seq, -8, 0) == 0

    def test_empty_sequence(self):
        assert get_item([], 0) is None
        assert get_item([], 3, "empty") == "empty"


class TestCheckAndNormalizeUrl:

    def test_empty_string(self):
        assert not _check_and_normalize_url("")

    def test_leading_and_trailing_whitespaces(self):
        assert not _check_and_normalize_url(" http://example.com")
        assert not _check_and_normalize_url("http://example.com ")
        assert not _check_and_normalize_url(" http://example.com ")

    def test_valid_protocols(self):
        assert _check_and_normalize_url("http://example.com") == "http://example.com/"
        assert _check_and_normalize_url("https://example.com/") == "https://example.com/"
        assert _check_and_normalize_url("ton://example.com") == "ton://example.com/"
        assert _check_and_normalize_url("tg://example.com") == "tg://example.com/"
        assert _check_and_normalize_url("tonsite://example.com") == "tonsite://example.com/"

    def test_no_protocol(self):    # No protocol
        assert _check_and_normalize_url("example.com") == "http://example.com/"

    def test_wrong_protocol_failing(self):
        assert not _check_and_normalize_url("ftp://example.com")
        assert not _check_and_normalize_url("htts://example.com")
        assert not _check_and_normalize_url("ws://example.com")

    def test_trailing_slash(self):
        assert _check_and_normalize_url("http://example.com") == "http://example.com/"
        assert _check_and_normalize_url("http://example.com/") == "http://example.com/"
        assert _check_and_normalize_url("http://example.com/path") == "http://example.com/path"
        assert _check_and_normalize_url("http://example.com/path/") == "http://example.com/path/"

    def test_with_newline_inside_failing(self):
        assert not _check_and_normalize_url("https://example\n.com")

    def test_http_urls_without_path_and_params(self):
        assert _check_and_normalize_url("http://example.com/") == "http://example.com/"
        assert _check_and_normalize_url("http://www.example.com/") == "http://www.example.com/"
        assert _check_and_normalize_url("http://www.example.com") == "http://www.example.com/"
        assert _check_and_normalize_url("www.example.com") == "http://www.example.com/"
        assert _check_and_normalize_url("www.example.com/") == "http://www.example.com/"

    def test_https_urls_without_path_and_params(self):
        assert _check_and_normalize_url("https://example.com/") == "https://example.com/"
        assert _check_and_normalize_url("https://www.example.com/") == "https://www.example.com/"
        assert _check_and_normalize_url("https://www.example.com") == "https://www.example.com/"

    def test_no_slash_at_the_end_of_the_url_with_params(self):
        assert _check_and_normalize_url("www.example.com/login") == "http://www.example.com/login"
        assert _check_and_normalize_url("https://example.com/login/") == "https://example.com/login/"


class TestSplitAndSortIntersectedEntities:
    def test_empty_entities(self):
        assert _split_and_sort_intersected_entities(()) == list()

    def test_non_intersected_entities(self):
        # The input string is "<b>bold</b> <i>italic</i> <u>underline</u>"
        in_seq = (MessageEntity(length=4, offset=0, type=MessageEntityType.BOLD),
                  MessageEntity(length=6, offset=5, type=MessageEntityType.ITALIC),
                  MessageEntity(length=9, offset=12, type=MessageEntityType.UNDERLINE))

        result = _split_and_sort_intersected_entities(in_seq)

        assert result == [MessageEntity(length=4, offset=0, type=MessageEntityType.BOLD),
                          MessageEntity(length=6, offset=5, type=MessageEntityType.ITALIC),
                          MessageEntity(length=9, offset=12, type=MessageEntityType.UNDERLINE)]

    def test_intersected_entities_case(self):
        # The input string is "<b>hello <i>italic <u>underlined <s>nested</s> entities</u> wo</i>rld</b>"
        in_seq = (MessageEntity(length=45, offset=0, type=MessageEntityType.BOLD),
                  MessageEntity(length=36, offset=6, type=MessageEntityType.ITALIC),
                  MessageEntity(length=26, offset=13, type=MessageEntityType.UNDERLINE),
                  MessageEntity(length=6, offset=24, type=MessageEntityType.STRIKETHROUGH))

        result = _split_and_sort_intersected_entities(in_seq)

        assert result == [MessageEntity(length=6, offset=0, type=MessageEntityType.BOLD),
                          MessageEntity(length=7, offset=6, type=MessageEntityType.BOLD),
                          MessageEntity(length=7, offset=6, type=MessageEntityType.ITALIC),
                          MessageEntity(length=11, offset=13, type=MessageEntityType.BOLD),
                          MessageEntity(length=11, offset=13, type=MessageEntityType.ITALIC),
                          MessageEntity(length=11, offset=13, type=MessageEntityType.UNDERLINE),
                          MessageEntity(length=21, offset=24, type=MessageEntityType.BOLD),
                          MessageEntity(length=18, offset=24, type=MessageEntityType.ITALIC),
                          MessageEntity(length=15, offset=24, type=MessageEntityType.UNDERLINE),
                          MessageEntity(length=6, offset=24, type=MessageEntityType.STRIKETHROUGH)]
