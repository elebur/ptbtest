import pytest
from telegram import MessageEntity
from telegram.constants import MessageEntityType

from ptbtest.entityparser import EntityParser


class TestParsePhoneNumbers:
    ep = EntityParser

    def test_empty_string(self):
        assert self.ep.parse_phone_numbers("") == ()

    def test_string_without_phone_number(self):
        assert self.ep.parse_phone_numbers("No numbers") == ()

    def test_valid_numbers_digits_only(self):
        assert self.ep.parse_phone_numbers("+2411234567") == (MessageEntity(length=11, offset=0, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+18117967070") == (MessageEntity(length=12, offset=0, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+24117967070") == (MessageEntity(length=12, offset=0, type=MessageEntityType.PHONE_NUMBER),)

    def test_too_long_numbers(self):
        assert self.ep.parse_phone_numbers("+1000000004002424230") == ()
        assert self.ep.parse_phone_numbers("+3000000004002424230") == ()
        assert self.ep.parse_phone_numbers("+2410000000017967070") == ()

    def test_exact_length(self):
        assert self.ep.parse_phone_numbers("+100000004002424231") == (MessageEntity(length=19, offset=0,
                                                                                    type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+300000004002424230") == (MessageEntity(length=19, offset=0,
                                                                                    type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+241000000017967070") == (MessageEntity(length=19, offset=0,
                                                                                    type=MessageEntityType.PHONE_NUMBER),)

    def test_too_short_numbers(self):
        assert self.ep.parse_phone_numbers("+1123") == ()
        assert self.ep.parse_phone_numbers("+1123456789") == ()
        assert self.ep.parse_phone_numbers("+241123456") == ()

    def test_valid_plus_sign(self):
        assert self.ep.parse_phone_numbers("++1-8011796707") == (MessageEntity(length=14, offset=0,
                                                                               type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+++1-8011796707") == (MessageEntity(length=14, offset=1,
                                                                                type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+(+1-801179670)7") == (MessageEntity(length=16, offset=0,
                                                                                 type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("((++++++++++++1-8011796707") == (MessageEntity(length=14, offset=12,
                                                                                           type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(++1-8011796707") == (MessageEntity(length=14, offset=1,
                                                                                type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+-+1456123(1)234") == (MessageEntity(length=16, offset=0,
                                                                                 type=MessageEntityType.PHONE_NUMBER),)

    def test_invalid_plus_sign(self):
        assert self.ep.parse_phone_numbers("+(+(+1-8011796707") == ()
        assert self.ep.parse_phone_numbers("((+1-8011796707") == ()
        assert self.ep.parse_phone_numbers("+(+1-8011796707") == ()
        assert self.ep.parse_phone_numbers("+(+1456123(1)234)") == ()
        assert self.ep.parse_phone_numbers("+-(+1456123(1)234)") == ()

    def test_without_plus_sign(self):
        assert self.ep.parse_phone_numbers("14561231234") == ()

    def test_valid_parentheses(self):
        assert self.ep.parse_phone_numbers("+(2)01234567890") == (MessageEntity(length=15, offset=0, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+1801179670)7") == (MessageEntity(length=14, offset=0, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+277798(746)54") == (MessageEntity(length=14, offset=0, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+1(801179)6707") == (MessageEntity(length=14, offset=0, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+14(5612)31234)") == (MessageEntity(length=14, offset=1, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+14561231234") == (MessageEntity(length=12, offset=1, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+14561231234") == (MessageEntity(length=12, offset=1, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+14561231234)") == (MessageEntity(length=12, offset=1, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+10000004002424230") == (MessageEntity(length=18, offset=1, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+)31779874654") == (MessageEntity(length=14, offset=0, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+145-6-1-2-3)1234(") == (MessageEntity(length=18, offset=0, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+145-6-1-2-3)1234()()") == (MessageEntity(length=18, offset=0, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+145-6-1-2-3-1-2-3-4") == (MessageEntity(length=20, offset=1, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+1-801179670)7") == (MessageEntity(length=15, offset=0, type=MessageEntityType.PHONE_NUMBER),)

    def test_invalid_parentheses(self):
        assert self.ep.parse_phone_numbers("+31(779874654") == ()
        assert self.ep.parse_phone_numbers("+31)779874654") == ()
        assert self.ep.parse_phone_numbers("+31)77(9874654") == ()
        assert self.ep.parse_phone_numbers("+1(8011796707)") == ()
        assert self.ep.parse_phone_numbers("(+31)77(9874654") == ()
        assert self.ep.parse_phone_numbers("((+14(5612)31234") == ()

    def test_valid_hyphens(self):
        assert self.ep.parse_phone_numbers("+-1-4-5-6-1-2-3-1234") == (MessageEntity(length=20, offset=0,
                                                                                     type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+145-6-1-2-3-1-2-3-4") == (MessageEntity(length=20, offset=0,
                                                                                     type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+145-6-1-2-3-1-2-3-4---------") == (MessageEntity(length=20, offset=0,
                                                                                              type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+1----811796707----0") == (MessageEntity(length=20, offset=0,
                                                                                     type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+245-779-87-4654") == (MessageEntity(length=16, offset=0,
                                                                                 type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+1--80-1-1-7-9-6-707") == (MessageEntity(length=20, offset=0,
                                                                                     type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+1-456-1231234") == (MessageEntity(length=14, offset=0,
                                                                               type=MessageEntityType.PHONE_NUMBER),)

    def test_invalid_hyphens(self):
        # Too many symbols (> 20).
        assert self.ep.parse_phone_numbers("+14-5-6-1-2-3-1-2-3-4") == ()
        assert self.ep.parse_phone_numbers("+1-----8117967070") == ()

    def test_valid_parentheses_and_hyphens(self):
        assert self.ep.parse_phone_numbers("+1-456123(1)234") == (MessageEntity(length=15, offset=0,
                                                                                type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+2-24456123(1)23") == (MessageEntity(length=16, offset=0,
                                                                                 type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+2-2-4456123(1)23") == (MessageEntity(length=17, offset=0,
                                                                                  type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+2-2-4-456123(1)23") == (MessageEntity(length=18, offset=0,
                                                                                   type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+2-2-4-456123(1)23") == (MessageEntity(length=18, offset=0,
                                                                                   type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+2-24-456123(1)23") == (MessageEntity(length=17, offset=0,
                                                                                  type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+1-801179670)7") == (MessageEntity(length=15, offset=0,
                                                                                type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+1--80-1-1-7-9-6-707") == (MessageEntity(length=20, offset=1,
                                                                                      type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+1--80-1179670)7") == (MessageEntity(length=17, offset=0,
                                                                                  type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+1--801179670)7") == (MessageEntity(length=16, offset=0,
                                                                                 type=MessageEntityType.PHONE_NUMBER),)

    @pytest.mark.xfail(reason="TODO. See docstring")
    def test_invalid_parentheses_and_hyphens(self):
        """
        This test fails. I don't know exactly why.
        It is something with hyphens and parentheses.
        If the parentheses are removed, then everything is working fine.
        Perhaps it is related to the number patterns (XX-XX-XX, XXX-XXXX, etc.),

        This tdlib->telegram->CountryInfoManager.cpp->get_phone_number_info_object
        might help or might not.

        """
        assert self.ep.parse_phone_numbers("+-1-4-5-6-1-23(12)234") == ()
        assert self.ep.parse_phone_numbers("+-1-4-5-6-1-23(1)234") == ()
        assert self.ep.parse_phone_numbers("+1-4-56123(1)234") == ()
        assert self.ep.parse_phone_numbers("+14-56123(1)234") == ()
        assert self.ep.parse_phone_numbers("+145-6123(1)234") == ()
        assert self.ep.parse_phone_numbers("+1-234(567)8901") == ()
        assert self.ep.parse_phone_numbers("+1-234(567)8901") == ()

    def test_zeros_between_country_code_and_number(self):
        assert self.ep.parse_phone_numbers("+100000004002424231") == (MessageEntity(length=19, offset=0,
                                                                                    type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+100004002424231") == (MessageEntity(length=16, offset=0,
                                                                                 type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("+104002424231") == (MessageEntity(length=13, offset=0,
                                                                              type=MessageEntityType.PHONE_NUMBER),)

    def test_parenthesis_at_the_beginning(self):
        # The maximum length.
        assert self.ep.parse_phone_numbers("(+10000004002424230") == (MessageEntity(length=18, offset=1, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+100000040024242303") == ()
        # The minimum length.
        assert self.ep.parse_phone_numbers("(+11234567890") == (MessageEntity(length=12, offset=1, type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("(+1123456789") == ()

    def test_non_0123456789_numbers(self):
        # These all symbols are valid numbers ("1૩５𝟔൭௯𝟵𝟿៩௫८"),
        # and regex's '\d' will match them, but Telegram expects numbers
        # to consist of 0-9 digits only.
        # A little more details on the numbers - https://stackoverflow.com/a/54912545/19813684
        assert self.ep.parse_phone_numbers("+1૩５𝟔൭௯𝟵𝟿៩௫८") == ()

    def test_whitespaces(self):
        assert self.ep.parse_phone_numbers("+1 8117967070") == ()
        assert self.ep.parse_phone_numbers("+1 811 7967070") == ()
        assert self.ep.parse_phone_numbers("+1 811 796 7070") == ()

    def test_embed_numbers(self):
        assert self.ep.parse_phone_numbers("123+348011796707") == (MessageEntity(length=13,
                                                                                 offset=3,
                                                                                 type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("text+180012(34)567;") == (MessageEntity(length=14,
                                                                                    offset=4,
                                                                                    type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("text+180012(34)567;") == (MessageEntity(length=14,
                                                                                    offset=4,
                                                                                    type=MessageEntityType.PHONE_NUMBER),)
        assert self.ep.parse_phone_numbers("tel:+180012(34)567;") == (MessageEntity(length=14,
                                                                                    offset=4,
                                                                                    type=MessageEntityType.PHONE_NUMBER),)

    def test_punctuation_and_hyphen_before_number(self):
        for ch in "([+":
            assert self.ep.parse_phone_numbers(ch+"-(+14561231234") == ()
        for ch in "!\"#$%&\')*,-./:;<=>?@\\]^_`{|}~":
            assert self.ep.parse_phone_numbers(ch+"-(+14561231234") == (MessageEntity(length=12, offset=3, type=MessageEntityType.PHONE_NUMBER),)

    def test_multiple_numbers_in_string(self):
        assert self.ep.parse_phone_numbers("tel:+180012(34)567; and phone:+298123456") == (MessageEntity(length=14,
                                                                                                         offset=4,
                                                                                                         type=MessageEntityType.PHONE_NUMBER),
                                                                                           MessageEntity(length=10,
                                                                                                         offset=30,
                                                                                                         type=MessageEntityType.PHONE_NUMBER))
        assert self.ep.parse_phone_numbers("+18001234567+18001234567") == (MessageEntity(length=12,
                                                                                         offset=0,
                                                                                         type=MessageEntityType.PHONE_NUMBER),
                                                                           MessageEntity(length=12,
                                                                                         offset=12,
                                                                                         type=MessageEntityType.PHONE_NUMBER))

    def test_letter_right_after_number(self):
        assert self.ep.parse_phone_numbers("+18001234567number") == ()
        assert self.ep.parse_phone_numbers("+18001234567 number") == (MessageEntity(length=12, offset=0, type=MessageEntityType.PHONE_NUMBER),)


    def test_newline_in_number(self):
        assert self.ep.parse_phone_numbers("+180012\n34567") == ()
