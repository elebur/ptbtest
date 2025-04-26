import re

import pytest

from ptbtest.entityparser import _decode_html_entity


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
                                                       ("&#174;", "®", 6),
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

