from ptbtest.entityparser import (_get_utf16_length,
                                  get_item,
                                  _check_and_normalize_url)


def test_get_utf_16_length():
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

    def test_wrong_protocol(self):
        assert not _check_and_normalize_url("ftp://example.com")
        assert not _check_and_normalize_url("htts://example.com")
        assert not _check_and_normalize_url("ws://example.com")

    def test_trailing_slash(self):
        assert _check_and_normalize_url("http://example.com") == "http://example.com/"
        assert _check_and_normalize_url("http://example.com/") == "http://example.com/"
        assert _check_and_normalize_url("http://example.com/path") == "http://example.com/path"
        assert _check_and_normalize_url("http://example.com/path/") == "http://example.com/path/"
