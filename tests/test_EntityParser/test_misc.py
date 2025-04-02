import pytest

from ptbtest.entityparser import (EntityParser,
                                  get_utf_16_length,
                                  get_item,
                                  check_and_normalize_url)


def test_get_utf_16_length():
    assert get_utf_16_length("a") == 1  # ASCII
    assert get_utf_16_length("hello") == 5  # Multiple ASCII symbols
    assert get_utf_16_length("€") == 1  # Euro (part of the BPM)
    assert get_utf_16_length("𐍈") == 2  # UTF-16 surrogate pair
    assert get_utf_16_length("👨‍👩‍👧‍👦") == 11 # Emoji wit ZWJ (Zero Width Joiner)
    assert get_utf_16_length("") == 0  # Empty string
    assert get_utf_16_length("👀🔥") == 4  # Two emojis (each has 2 UTF-16 units)


class TestMessagesWithoutEntities:
    ep = EntityParser()
    def test_one_line(self):
        text = "A string without any entity"
        resp = self.ep.parse_markdown(text)
        assert resp == ('A string without any entity', ())

    def test_multiline(self):
        text = "A multi\nline string without\n any entity"
        resp = self.ep.parse_markdown(text)
        assert resp == ('A multi\nline string without\n any entity', ())

    def test_escaped_symbols(self):
        text = ("A multi\nline string without\n any entity\n"
                "but with escaped \[ entity's \` symbols \* in it\_")
        resp = self.ep.parse_markdown(text)
        assert resp == ("A multi\nline string without\n any entity\nbut with escaped [ entity's ` symbols * in it_", ())

    @pytest.mark.parametrize("input, result", (
            ("    A string with a whitespace at the beginning.", "A string with a whitespace at the beginning."),
            ("A string with a whitespace at the end.    ", "A string with a whitespace at the end."),
            ("    Leading and trailing whitespaces   ", "Leading and trailing whitespaces"),
            ("   multiline string        \n    where each line has     \n    leading and trailing whitespaces      ",
                "multiline string        \n    where each line has     \n    leading and trailing whitespaces"),
    ))
    def test_whitespace(self, input, result):
        resp = self.ep.parse_markdown(input)
        assert resp == (result, ())


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
        assert not check_and_normalize_url("")

    def test_leading_and_trailing_whitespaces(self):
        assert not check_and_normalize_url(" http://example.com")
        assert not check_and_normalize_url("http://example.com ")
        assert not check_and_normalize_url(" http://example.com ")

    def test_valid_protocols(self):
        assert check_and_normalize_url("http://example.com") == "http://example.com/"
        assert check_and_normalize_url("https://example.com/") == "https://example.com/"
        assert check_and_normalize_url("ton://example.com") == "ton://example.com/"
        assert check_and_normalize_url("tg://example.com") == "tg://example.com/"
        assert check_and_normalize_url("tonsite://example.com") == "tonsite://example.com/"

    def test_no_protocol(self):    # No protocol
        assert check_and_normalize_url("example.com") == "http://example.com/"

    def test_wrong_protocol(self):
        assert not check_and_normalize_url("ftp://example.com")
        assert not check_and_normalize_url("htts://example.com")
        assert not check_and_normalize_url("ws://example.com")

    def test_trailing_slash(self):
        assert check_and_normalize_url("http://example.com") == "http://example.com/"
        assert check_and_normalize_url("http://example.com/") == "http://example.com/"
        assert check_and_normalize_url("http://example.com/path") == "http://example.com/path"
        assert check_and_normalize_url("http://example.com/path/") == "http://example.com/path/"
