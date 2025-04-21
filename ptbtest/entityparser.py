# A library that provides a testing suite fot python-telegram-bot
# which can be found on https://github.com/python-telegram-bot/python-telegram-bot
# Copyright (C) 2017
# Pieter Schutz - https://github.com/eldinnie
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
"""
This module provides a helper class to transform
marked-up messages to plain text and a :obj:`tuple` of
:class:`entities <telegram.MessageEntity>`.

`Telegram Docs <https://core.telegram.org/bots/api#formatting-options>`_
"""
import re
from collections.abc import Sequence
from typing import Any, Literal, Optional
from urllib.parse import urlparse

from telegram import MessageEntity, TelegramObject
from telegram.constants import MessageEntityType

from ptbtest.errors import BadMarkupException

# These priorities are used for sorting purpose.
# https://github.com/tdlib/td/blob/f1b7500310baa496c0b779e4273a3aff0f14f42f/td/telegram/MessageEntity.cpp#L38
PRIORITIES = {
    MessageEntityType.MENTION: 50,
    MessageEntityType.HASHTAG: 50,
    MessageEntityType.BOT_COMMAND: 50,
    MessageEntityType.URL: 50,
    MessageEntityType.EMAIL: 50,
    MessageEntityType.BOLD: 90,
    MessageEntityType.ITALIC: 91,
    MessageEntityType.CODE: 20,
    MessageEntityType.PRE: 10,
    MessageEntityType.TEXT_LINK: 49,
    MessageEntityType.TEXT_MENTION: 49,
    MessageEntityType.CASHTAG: 50,
    MessageEntityType.PHONE_NUMBER: 50,
    MessageEntityType.UNDERLINE: 92,
    MessageEntityType.STRIKETHROUGH: 93,
    MessageEntityType.BLOCKQUOTE: 0,
    MessageEntityType.SPOILER: 94,
    MessageEntityType.CUSTOM_EMOJI: 99,
    MessageEntityType.EXPANDABLE_BLOCKQUOTE: 0
}


def _get_utf16_length(text: str) -> int:
    """
    Return the length of the ``text`` in UTF-16 code units.

    Telegram `uses UTF-16 <https://core.telegram.org/api/entities#utf-16>`_
    for message entities

    A simple way of computing the entity length is converting the text to UTF-16,
    and then taking the byte length divided by 2 (number of UTF-16 code units).
    `Source <https://core.telegram.org/api/entities#computing-entity-length>`_

    :param text: (`type`: :obj:`str`) A string to calculate the length for.

    :return: (`type`: :obj:`int`) The length of the given string.
    """
    return len(text.encode("utf-16-le")) // 2


def get_item(seq: Sequence, index: int, default: Any = None) -> Any:
    """
    Safely gets item from the sequence by its index.
    If the ``index`` is out of the range, then the ``default`` value is returned.

    :param seq: (`type`: :obj:`~collections.abc.Sequence`) A sequence to get the item from.
    :param index: (`type`: :obj:`int`) An item's index.
    :param default: (`type`: :obj:`~typing.Any`) The value to be returned if the
        ``index`` is out of the range, defaults to :obj:`None`.
    :return: (`type`: :obj:`~typing.Any`) An item under the given ``index`` or
        the ``default`` value.
    """
    # An empty sequence.
    if not seq:
        return default

    # The positive index, but it is out of the range.
    if index > 0 and index >= len(seq):
        return default

    # The negative index, but it is out of the range.
    if index < 0 and abs(index) > len(seq):
        return default

    return seq[index]


def _check_and_normalize_url(url: str) -> str:
    """
    Check whether the ``url`` is valid, according to Telegram rules.

    :param url: (`type`: :obj:`str`) The ``url`` to be checked.
    :return: (`type`: :obj:`str`) Empty string if the ``url`` is invalid,
        normalized URL otherwise.
    """
    if not url or url.startswith(" ") or url.endswith(" "):
        return ""

    result = url

    # If the protocol is not specified, sets 'http' protocol
    if "://" not in result:
        result = "http://" + result

    try:
        parsed_url = urlparse(result)
    except ValueError:
        return ""

    if parsed_url.scheme not in ("http", "https", "ton", "tg", "tonsite"):
        return ""

    # Validate domain name.
    pattern_valid_domain = re.compile(r"^(?=.{1,255}$)(?!-)[A-Za-z0-9\-]{1,63}"
                                      r"(\.[A-Za-z0-9\-]{1,63})*\.?(?<!-)$")
    if not pattern_valid_domain.match(parsed_url.netloc):
        return ""

    # Adding trailing slash only for URLs without a path.
    # E.g., https://www.example.com - adds the slash.
    # https://www.example.com/login - doesn't add the slash.
    if not parsed_url.path and not result.endswith("/"):
        result += "/"

    return result


def _get_id_from_telegram_url(type_: Literal["user", "emoji"], url: str) -> Optional[int]:
    """
    Extract a user or emoji ID from the Telegram URL.

    Examples of URLs: ``tg://user?id=123456789``, ``tg://emoji?id=5368324170671202286``

    :param type_: (`type`: :obj:`str`) One of `user` or `emoji`. Depends on
        the ID that must be extracted.
    :param url: (`type`: :obj:`str`) A URL to extract the ID from.
    :return: (`type`: :obj:`~typing.Optional` [:obj:`int`]) Extracted ID or :obj:`None` if no
        ID was found.
    """
    if type_ not in ("user", "emoji"):
        raise ValueError(f"Wrong type - {type_}")

    id_ = None
    if match := re.match(rf"tg://{type_}\?id=(\d+)", url):
        id_ = int(match.group(1))

    return id_


def get_hash(obj: TelegramObject) -> int:
    """
    Generate the unique hash value for objects that are inherited
    from :obj:`~telegram.TelegramObject`.

    The :meth:`telegram.TelegramObject.__hash__` method considers only certain
    attributes described in ``_id_attrs``.

    E.g., the ``_id_attrs`` of :obj:`~telegram.MessageEntity` is
    ``(self.type, self.offset, self.length)``.
    It means that ``MessageEntity("url", 1, 2)``
    and ``MessageEntity("url", 1, 2, url="https://ex.com)`` are equal and get the same hash.

    The ``get_hash`` function transforms ``obj`` into a JSON string
    and then gets hash of that string.

    :param obj: (`type`: :obj:`~telegram.TelegramObject`) An object to generate hash for.
    :return: (`type`: :obj:`int`) A hash value for the given object.
    """
    return hash(obj.to_json())


def _split_entities(nested_entities: Sequence[MessageEntity],
                    incoming_entity: MessageEntity,
                    raw_offset: dict[int, int]) -> (list[MessageEntity, ...], list[MessageEntity, ...]):
    """
    The function splits all unclosed entities if a new entity is coming.
    Therefore, the ``parse_markdown_v2`` function will return the same result as
    the Telegram server does.

    Example:
        An input string is ``*hello _italic ~world~ italic_ world*``.

        By default, :meth:`~ptbtest.entityparser.EntityParser.parse_markdown_v2` returns:

        .. code:: python

            MessageEntity(length=31, offset=0, type=MessageEntityType.BOLD)
            MessageEntity(length=19, offset=6, type=MessageEntityType.ITALIC)
            MessageEntity(length=5, offset=13, type=MessageEntityType.STRIKETHROUGH)

        For the same string, the Telegram server returns:

        .. code:: python

            MessageEntity(length=6, offset=0, type=MessageEntityType.BOLD)
            MessageEntity(length=7, offset=6, type=MessageEntityType.BOLD)
            MessageEntity(length=7, offset=6, type=MessageEntityType.ITALIC)
            MessageEntity(length=18, offset=13, type=MessageEntityType.BOLD)
            MessageEntity(length=12, offset=13, type=MessageEntityType.ITALIC)
            MessageEntity(length=5, offset=13, type=MessageEntityType.STRIKETHROUGH)

    Args:
        nested_entities (Sequence[~telegram.MessageEntity]): A list of all unclosed entities.
        incoming_entity (~telegram.MessageEntity): New entity that must be added to the
            ``nested_entity``.
        raw_offset (dict[int, int]): A dictionary, that stores a byte offset (the beginning
            position) of entities. The key is the entity's hash and the value is
            the byte offset.

    Returns:
        (list[~telegram.MessageEntity], list[~telegram.MessageEntity]):
            Two lists. The first one is the updated ``nested_entities`` list and the second
            on is the list of closed entities that must be added to the final list
            of entities.
    """
    new_nested = []
    closed_entities = []
    for ent in nested_entities:
        # Links and quotes mustn't be split.
        if ent.type in (MessageEntityType.TEXT_LINK, MessageEntityType.BLOCKQUOTE ):
            new_nested.append(ent)
            continue
        # MessageEntity can't be edited directly.
        # First it is transformed into the dict object, then the dict is edited,
        # and then new MessageEntity is created from this dict.
        ent_dict = ent.to_dict()
        original_length = ent.length
        new_length = incoming_entity.offset - ent.offset
        if new_length > 0:
            ent_dict["length"] = new_length
            closed_entities.append(MessageEntity(**ent_dict))

        ent_dict["offset"] = incoming_entity.offset
        ent_dict["length"] = original_length - new_length

        new_ent = MessageEntity(**ent_dict)
        # Updating the entity's byte offset in the original string
        # (the position where the entity is started).
        # The byte offset is linked to the original entity,
        # but it will be removed after splitting.
        # Here the offset is relinked from the original entity to the new one.
        raw_offset[get_hash(new_ent)] = raw_offset[get_hash(ent)]
        new_nested.append(new_ent)

    new_nested.append(incoming_entity)

    return new_nested, closed_entities


class EntityParser:
    @staticmethod
    def parse_markdown(text: str) -> tuple[str, tuple[MessageEntity, ...]]:
        """
        Extract :obj:`~telegram.MessageEntity` from ``text`` with the
        `Markdown V1 <https://core.telegram.org/bots/api#markdown-style>`_ markup.

        Examples:
            An input string: ``*hello* _world_ `!```

            Result:

            .. code:: python

                ('hello world !',
                 (MessageEntity(length=5, offset=0, type=<MessageEntityType.BOLD>),
                  MessageEntity(length=5, offset=6, type=<MessageEntityType.ITALIC>),
                  MessageEntity(length=1, offset=12, type=<MessageEntityType.CODE>)))

        Args:
            text (str): A string with Markdown V1 markup.

        Returns:
            (str, tuple(~telegram.MessageEntity)): The clean string without entity
            symbols, and tuple with :obj:`~telegram.MessageEntity`.
        """
        entities = list()
        striped_text = text.strip()
        text_size = len(striped_text)
        utf16_offset = 0
        new_text = list()

        # https://github.com/TelegramMessenger/libprisma#supported-languages
        pre_code_language_pattern = re.compile(r"^([a-z0-9-]+)\s+")

        i = 0
        while i < text_size:
            ch = striped_text[i]
            if ch == "\\" and get_item(striped_text, i+1) in "_*`[":
                # Skip the escape symbol (\).
                i += 1
                new_text.append(striped_text[i])
                # Go to the next char in the given string.
                i += 1
                utf16_offset += 1
                continue

            # Current char is NOT an entity beginning.
            # Save it 'as is' and go on to the next char
            if ch not in "_*`[":
                # Here it might be any symbol, and it can have any length.
                # E.g. 'A' has 1 code unit, '©' has 1 code unit, '😊' has 2 code units.
                utf16_offset += _get_utf16_length(ch)
                new_text.append(ch)
                i += 1
                continue

            # Telegram returns error messages with the offset specified in bytes.
            # The length of strings and byte strings might be different. E.g.:
            # len('A©😊') == 3, while len('A©😊'.encode()) == 7.
            # This value is used only for the error message.
            begin_index_utf16 = len(striped_text[:i].encode())
            end_character = ch

            if ch == "[":
                end_character = "]"

            # Skipping the entity's opening char.
            i += 1
            language = ""

            is_pre = False
            if ch == "`" and i + 2 < text_size and striped_text[i:i+2] == "``":
                # The code entity has three chars (```).
                # The first one was skipped the few lines above
                # (`i += 1` just above this `if`).
                # Increasing the counter by 2 to skip the rest of the entity's
                # symbols and jump to the text.
                i += 2
                is_pre = True
                # Trying to get language name.
                # E.g.:
                # ```python <- this name
                # code snippet here
                # ```
                if lang_match := pre_code_language_pattern.match(striped_text[i:]):
                    # .group(0) contains trailing space too.
                    # .group(1) contains the language name only.
                    language = lang_match.group(1)
                    i += len(language)

                if striped_text[i] in "\r\n":
                    i += 1

            entity_offset = utf16_offset

            entity_content_pattern = fr"^(.*?)\{end_character}"
            if is_pre:
                entity_content_pattern = r"^(.*?)```"

            # Here we parse all content inside the entity
            # up to closing symbol (which is not included).
            if entity_content_match := re.match(entity_content_pattern,
                                                striped_text[i:],
                                                re.DOTALL):
                entity_end_char = "```" if is_pre else end_character
                entity_content = (entity_content_match.group()
                                  .removesuffix(entity_end_char))
                i += len(entity_content)

                # If this is the end of the message, then remove ALL trailing
                # whitespaces and new line characters.
                if i + len(entity_end_char) == text_size:
                    entity_content = entity_content.rstrip()

                # If the current entity is a link (starts with '[')...
                if ch == "[":
                    # ... and there is a whitespace or a newline between
                    # square brackets and parentheses
                    if re.match(r"^]\s+\([^)]+\)", striped_text[i:]):
                        # Saving the content of the square brackets 'as is'.
                        new_text.append(entity_content)
                        # `+1` here is the length of the entity's end char (`]`).
                        i += 1
                        continue
                    # ... or if there is nothing after the entity or there are
                    # only whitespaces, then remove all whitespaces at the end
                    # of the string.
                    # Here the trailing whitespace WON'T be striped:
                    # `[inline URL ](http://www.example.com) with trailing text.`
                    # While here the whitespace WILL be striped:
                    # `[inline URL ](http://www.example.com)`
                    elif (get_item(striped_text, i + 1) == "(" and
                            not re.match(r"^]\(.*?\)\s*\S.*", striped_text[i:])):
                        entity_content = entity_content.rstrip()

                utf16_offset += _get_utf16_length(entity_content)
                new_text.append(entity_content)
            # The code reached the end of the text, but the end
            # of the entity wasn't found.
            if i == text_size or not entity_content_match:
                # `telegram.Bot` raises `telegram.error.BadRequest` error.
                raise BadMarkupException(f"Can't parse entities: can't find end of the entity "
                                         f"starting at byte offset {begin_index_utf16}")

            if entity_offset != utf16_offset:
                entity_length = utf16_offset - entity_offset
                if ch == "_":
                    entities.append(MessageEntity(MessageEntity.ITALIC,
                                                  entity_offset,
                                                  entity_length))
                elif ch == "*":
                    entities.append(MessageEntity(MessageEntity.BOLD,
                                                  entity_offset,
                                                  entity_length))
                elif ch == "[":
                    url = ""
                    if get_item(striped_text, i + 1) == "(":
                        i += 2
                        while i < text_size and striped_text[i] != ")":
                            url += striped_text[i]
                            i += 1
                    # If there is no part with the URL (only square brackets:
                    # `[no URL part here]`) and the current entity is the only
                    # entity for now (the left most in the text), then we must strip
                    # all whitespaces at the beginning of the string.
                    else:
                        if len(new_text) == 1:
                            new_text[-1] = new_text[-1].lstrip()

                    if checked_url := _check_and_normalize_url(url):
                        # By some reason Markdown V1 ignores inline mentions.
                        # E.g.: [inline mention of a user](tg://user?id=123456789)
                        if not checked_url.startswith("tg://"):
                            entities.append(MessageEntity(MessageEntity.TEXT_LINK,
                                                          entity_offset,
                                                          entity_length,
                                                          url=checked_url))
                elif ch == "`":
                    if is_pre:
                        entities.append(MessageEntity(MessageEntity.PRE,
                                                      entity_offset,
                                                      entity_length,
                                                      language=language))

                    else:
                        entities.append(MessageEntity(MessageEntity.CODE,
                                                      entity_offset,
                                                      entity_length))

            if is_pre:
                i += 2
            i += 1

        result_str = "".join(new_text).rstrip()
        if not result_str:
            raise BadMarkupException("Text must be non-empty")

        return result_str, tuple(entities)

    @staticmethod
    def parse_markdown_v2(text: str) -> tuple[str, tuple[MessageEntity, ...]]:
        """
        Extract :obj:`~telegram.MessageEntity` from ``text`` with the
        `Markdown V2 <https://core.telegram.org/bots/api#markdownv2-style>`_ markup.

        Examples:
            An input string: ``*hello _nested __entities__ beautiful_ world*``

            Result:

            .. code:: python

                ('hello nested entities beautiful world',
                 (MessageEntity(length=6, offset=0, type=<MessageEntityType.BOLD>),
                  MessageEntity(length=7, offset=6, type=<MessageEntityType.BOLD>),
                  MessageEntity(length=7, offset=6, type=<MessageEntityType.ITALIC>),
                  MessageEntity(length=24, offset=13, type=<MessageEntityType.BOLD>),
                  MessageEntity(length=18, offset=13, type=<MessageEntityType.ITALIC>),
                  MessageEntity(length=8, offset=13, type=<MessageEntityType.UNDERLINE>)))

        Args:
            text (str): A string with Markdown V2 markup.

        Returns:
            (str, tuple(~telegram.MessageEntity)): The clean string without entity
            symbols, and tuple with :obj:`~telegram.MessageEntity`.
        """
        err_msg_entity = ("Can't parse entities: can't find end of "
                          "{entity_type} entity at byte offset {offset}")
        err_msg_reserved = ("Can't parse entities: character '{0}' is reserved "
                            "and must be escaped with the preceding '\\'")
        err_empty_text = "Message text is empty"

        have_blockquote = False
        can_start_blockquote = True

        striped_text = text.strip()

        offset = 0
        utf16_offset = 0
        text_size = len(striped_text)

        entities: list[MessageEntity] = list()
        nested_entities: list[MessageEntity] = list()
        result_text = ""
        # In this dict, the raw byte offset (the entity's start position
        # in the original string) of the entity will be stored.
        # The key is the entity's hash, and the value is the byte offset.
        # This dict will be used for error messages.
        raw_offset: dict[int, int] = dict()
        while offset < text_size:
            cur_ch = striped_text[offset]
            next_ch = get_item(striped_text, offset+1)
            # Processing escaped ASCII characters.
            if cur_ch == "\\" and 0 < ord(next_ch) <= 126:
                offset += 1
                result_text += striped_text[offset]
                utf16_offset += 1
                if striped_text[offset] != "\r":
                    can_start_blockquote = (striped_text[offset] == "\n")
                offset += 1
                continue

            reserved_characters = "_*[]()~`>#+-=|{}.!\n"
            if nested_entities:
                if nested_entities[-1].type in (MessageEntityType.CODE, MessageEntityType.PRE):
                    reserved_characters = "`"

            # Processing regular characters.
            if cur_ch not in reserved_characters:
                utf16_offset += _get_utf16_length(cur_ch)
                if cur_ch != "\r":
                    can_start_blockquote = False
                result_text += cur_ch
                offset += 1
                continue

            def is_end_of_entity() -> bool:
                """
                Check whether the current character is the one that closes the entity.
                """
                nonlocal text_size, offset, striped_text, cur_ch, have_blockquote, nested_entities

                if not nested_entities:
                    return False
                if (have_blockquote and cur_ch == "\n" and
                        (offset + 1 == text_size or get_item(striped_text, offset + 1) != ">")):
                    return True

                last_nested_entity_type = nested_entities[-1].type
                if last_nested_entity_type == MessageEntityType.BOLD:
                    is_end = (cur_ch == "*")
                elif last_nested_entity_type == MessageEntityType.ITALIC:
                    is_end = (cur_ch == "_" and get_item(striped_text, offset + 1) != "_")
                elif last_nested_entity_type == MessageEntityType.CODE:
                    is_end = (cur_ch == "`")
                elif last_nested_entity_type == MessageEntityType.PRE:
                    is_end = (cur_ch == "`"
                                        and get_item(striped_text, offset + 1) == "`"
                                        and get_item(striped_text, offset + 2) == "`")
                elif last_nested_entity_type == MessageEntityType.TEXT_LINK:
                    is_end = (cur_ch == "]")
                elif last_nested_entity_type == MessageEntityType.UNDERLINE:
                    is_end = (cur_ch == "_" and get_item(striped_text, offset + 1) == "_")
                elif last_nested_entity_type == MessageEntityType.STRIKETHROUGH:
                    is_end = (cur_ch == "~")
                elif last_nested_entity_type == MessageEntityType.SPOILER:
                    is_end = (cur_ch == "|" and get_item(striped_text, offset + 1) == "|")
                elif last_nested_entity_type == MessageEntityType.CUSTOM_EMOJI:
                    is_end = (cur_ch == "]")
                elif last_nested_entity_type == MessageEntityType.BLOCKQUOTE:
                    is_end = False
                else:
                    is_end = False

                return is_end

            user_id = None
            custom_emoji_id = None
            language = None
            url = None

            if not is_end_of_entity():
                entity_type: MessageEntityType = None
                entity_raw_begin_pos = offset
                if cur_ch == "_":
                    if get_item(striped_text, offset+1) == "_":
                        entity_type = MessageEntityType.UNDERLINE
                        offset += 1
                    else:
                        entity_type = MessageEntityType.ITALIC
                elif cur_ch == "*":
                    entity_type = MessageEntityType.BOLD
                elif cur_ch == "~":
                    entity_type = MessageEntityType.STRIKETHROUGH
                elif cur_ch == "|":
                    if get_item(striped_text, offset+1) == "|":
                        offset += 1
                        entity_type = MessageEntityType.SPOILER
                    else:
                        raise BadMarkupException(err_msg_reserved.format("|"))
                elif cur_ch == "[":
                    entity_type = MessageEntityType.TEXT_LINK
                elif cur_ch == "`":
                    if get_item(striped_text, offset+1) == "`" and get_item(striped_text, offset+2) == "`":
                        offset += 3
                        entity_type = MessageEntityType.PRE
                        # Trying to get language name.
                        # E.g.:
                        # ```python <- this name
                        # code snippet here
                        # ```
                        if lang_match := re.match(r"^([^\s`]+)\s+", striped_text[offset:]):
                            # .group(0) contains trailing space too.
                            # .group(1) contains the language name only.
                            language = lang_match.group(1)
                            offset += len(language)

                        # Without this condition, a whitespace right after the language
                        # name will be eaten.
                        if get_item(striped_text, offset, "") not in "\r\n":
                            offset -= 1
                    else:
                        entity_type = MessageEntityType.CODE
                elif cur_ch == "!":
                    if get_item(striped_text, offset+1) == "[":
                        offset += 1
                        entity_type = MessageEntityType.CUSTOM_EMOJI
                    else:
                        raise BadMarkupException(err_msg_reserved.format("!"))
                elif cur_ch == "\n":
                    utf16_offset += 1
                    result_text += cur_ch
                    can_start_blockquote = True
                elif cur_ch == ">":
                    if can_start_blockquote:
                        if not have_blockquote:
                            entity_type = MessageEntityType.BLOCKQUOTE
                            have_blockquote = True
                    else:
                        raise BadMarkupException(err_msg_reserved.format(">"))
                else:
                    raise BadMarkupException(err_msg_reserved.format(striped_text[offset]))

                if entity_type is None:
                    offset += 1
                    continue

                me = MessageEntity(type=entity_type, offset=utf16_offset,
                                   length=len(result_text) - utf16_offset,
                                   url=url, user=user_id, language=language,
                                   custom_emoji_id=custom_emoji_id)

                # By default, the error message for an empty string
                # is "Message text is empty", but if there was at least
                # one entity, the text changes to "text must be non-empty".
                if err_empty_text == "Message text is empty":
                    err_empty_text = "Text must be non-empty"

                nested_entities, closed_entities = _split_entities(nested_entities, me, raw_offset)
                entities.extend(closed_entities)

                raw_offset[get_hash(me)] = len(striped_text[:entity_raw_begin_pos].encode())

            else:
                # lne stands for last_nested_entity
                lne = nested_entities[-1]
                e_type = lne.type

                if cur_ch == "\n" and e_type != MessageEntityType.BLOCKQUOTE:
                    if (e_type != MessageEntityType.SPOILER or
                            not (lne.offset == offset - 2 or
                                    (lne.offset == offset - 3 and len(result_text) != 0 and result_text[-1] == "\r"))):
                        raise BadMarkupException(err_msg_entity.format(entity_type=e_type, offset=lne.offset))
                    nested_entities.pop()

                    lne = nested_entities[-1]
                    if lne.type != MessageEntityType.BLOCKQUOTE:
                        raise BadMarkupException(err_msg_entity.format(entity_type=lne.type,
                                                                       offset=lne.offset))
                    e_type = MessageEntityType.EXPANDABLE_BLOCKQUOTE

                skip_entity = (utf16_offset == lne.offset)
                if e_type in (MessageEntityType.BOLD, MessageEntityType.ITALIC,
                              MessageEntityType.CODE, MessageEntityType.STRIKETHROUGH):
                    pass
                elif e_type in (MessageEntityType.UNDERLINE, MessageEntityType.SPOILER):
                    offset += 1
                elif e_type == MessageEntityType.PRE:
                    offset += 2
                elif e_type == MessageEntityType.TEXT_LINK:
                    url = ""
                    if get_item(striped_text, offset+1) != "(":
                        url = result_text[lne.offset: len(result_text) - lne.offset]
                    else:
                        offset += 2
                        url_begin_pos = len(striped_text[:offset].encode())
                        while offset < text_size and striped_text[offset] != ")":
                            if cur_ch == "\\" and 0 < ord(next_ch) <= 126:
                                url += striped_text[offset + 1]
                                offset += 2
                                continue
                            url += striped_text[offset]
                            offset += 1
                        if get_item(striped_text, offset) != ")":
                            msg = "Can't parse entities: can't find end of a url at byte offset %s"
                            raise BadMarkupException(msg % url_begin_pos)

                    user_id = _get_id_from_telegram_url("user", url)
                    # As for April 2025, inline mentioning doesn't work (from the server side).
                    # If mentioning was found, skip it.
                    if user_id is not None:
                        user_id = None
                        skip_entity = True
                    else:
                        url = _check_and_normalize_url(url)
                        if not url:
                            skip_entity = True
                elif e_type == MessageEntityType.CUSTOM_EMOJI:
                    if get_item(striped_text, offset+1) != "(":
                        raise BadMarkupException("Custom emoji entity must contain a tg://emoji URL")
                    offset += 2
                    url = ""
                    url_begin_pos = offset

                    while offset < text_size and striped_text[offset] != ")":
                        if cur_ch == "\\" and 0 < ord(next_ch) <= 126:
                            url += striped_text[offset + 1]
                            offset += 2
                            continue
                        url += striped_text[offset]
                        offset += 1
                    if striped_text[offset] != ")":
                        raise BadMarkupException(f"Can't find end of a custom emoji URL at byte offset {url_begin_pos}")

                    custom_emoji_id = _get_id_from_telegram_url("emoji", url)
                elif e_type in (MessageEntityType.BLOCKQUOTE, MessageEntityType.EXPANDABLE_BLOCKQUOTE):
                    have_blockquote = False
                    result_text += striped_text[offset]
                    can_start_blockquote = True
                    utf16_offset += 1
                    skip_entity = False
                else:
                    raise BadMarkupException(f"Unknown entity '{e_type}' type is received.")

                if not skip_entity:
                    entity_offset = nested_entities[-1].offset
                    entity_length = utf16_offset - entity_offset
                    if user_id:
                        e_type = MessageEntityType.MENTION
                    elif custom_emoji_id:
                        e_type = MessageEntityType.CUSTOM_EMOJI

                    entities.append(MessageEntity(e_type,
                                                  entity_offset,
                                                  entity_length,
                                                  user=user_id,
                                                  custom_emoji_id=custom_emoji_id,
                                                  url=url,
                                                  language=lne.language))

                nested_entities.pop()

            offset += 1

        if have_blockquote:
            e_type = MessageEntityType.BLOCKQUOTE
            if nested_entities:
                lne = nested_entities[-1]
                if lne.type == MessageEntityType.SPOILER and lne.offset == len(result_text.encode()):
                    nested_entities.pop()
                    del lne
                    e_type = MessageEntityType.EXPANDABLE_BLOCKQUOTE

                lne = nested_entities[-1]
                if lne.type == MessageEntityType.BLOCKQUOTE:
                    entity_offset = lne.offset
                    entity_length = utf16_offset - entity_offset
                    if entity_length > 0:
                        entities.append(MessageEntity(e_type,
                                                      entity_offset,
                                                      entity_length))
                    nested_entities.pop(-1)

        if nested_entities:
            byte_offset = raw_offset[get_hash(nested_entities[-1])]
            entity_type = nested_entities[-1].type
            # Telegram has two different entities which are 'pre' and 'precode',
            # while PTB has only 'pre'.
            # 'pre' for code WITHOUT 'language' specified, and
            # 'precode' for code WITH 'language'
            if entity_type == MessageEntityType.PRE and nested_entities[-1].language:
                entity_type = "precode"
            raise BadMarkupException(err_msg_entity.format(entity_type=entity_type,
                                                           offset=byte_offset))
        len_before_strip = len(result_text)
        result_text = result_text.rstrip()
        # There were trailing new lines or whitespaces.
        if entities and len_before_strip != len(result_text):
            last_entity = entities[-1]
            # Trailing whitespaces were inside an entity, we must subtract
            # the length of striped whitespaces from the length of the entity.
            if len_before_strip == last_entity.offset + last_entity.length:
                d = last_entity.to_dict()
                d["length"] -= (len_before_strip - len(result_text))
                if d["length"] > 0:
                    entities[-1] = MessageEntity(**d)
                else:
                    entities.pop()

        if not result_text:
            raise BadMarkupException(err_empty_text)

        sorted_entities = sorted(entities, key=lambda m: (m.offset, -m.length, PRIORITIES[m.type]))
        if not sorted_entities:
            result_text = result_text.strip()

        return result_text, tuple(sorted_entities)

    @staticmethod
    def parse_html(message):
        """

        Args:
            message (str): Message with HTML text to be transformed

        Returns:
            (message(str), entities(list(telegram.MessageEntity))): The entities found in the message and
            the message after parsing.
        """
        invalids = re.compile(r'''(<b><i>|<b><pre>|<b><code>|<b>(<a.*?>)|
                                   <i><b>|<i><pre>|<i><code>|<i>(<a.*?>)|
                                   <pre><b>|<pre><i>|<pre><code>|<pre>(<a.*?>)|
                                   <code><b>|<code><i>|<code><pre>|<code>(<a.*?>)|
                                   (<a.*>)?<b>|(<a.*?>)<i>|(<a.*?>)<pre>|(<a.*?>)<code>)'''
                              )
        tags = re.compile(r'(<(b|i|pre|code)>(.*?)<\/\2>)')
        text_links = re.compile(
            r'<a href=[\'\"](?P<url>.*?)[\'\"]>(?P<text>.*?)<\/a>')

        return EntityParser.__parse_text("HTML", message, invalids, tags,
                                         text_links)

    @staticmethod
    def __parse_text(ptype, message, invalids, tags, text_links):
        entities = []
        mentions = re.compile(r'@[a-zA-Z0-9]{1,}\b')
        hashtags = re.compile(r'#[a-zA-Z0-9]{1,}\b')
        botcommands = re.compile(r'(?<!\/|\w)\/[a-zA-Z0-0_\-]{1,}\b')
        urls = re.compile(
            r'(([hHtTpP]{4}[sS]?|[fFtTpP]{3})://)?([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'
        )
        inv = invalids.search(message)
        if inv:
            raise BadMarkupException(
                "nested {} is not supported. your text: {}".format(
                    ptype, inv.groups()[0]))
        while tags.search(message):
            tag = tags.search(message)
            text = tag.groups()[2]
            start = tag.start()
            if tag.groups()[1] in ["b", "*"]:
                parse_type = "bold"
            elif tag.groups()[1] in ["i", "_"]:
                parse_type = "italic"
            elif tag.groups()[1] in ["code", "`"]:
                parse_type = "code"
            elif tag.groups()[1] in ["pre", "```"]:
                parse_type = "pre"
            entities.append(MessageEntity(parse_type, start, len(text)))
            message = tags.sub(r'\3', message, count=1)
        while text_links.search(message):
            link = text_links.search(message)
            url = link.group('url')
            text = link.group('text')
            start = link.start()
            length = len(text)
            for x, ent in enumerate(entities):
                if ent.offset > start:
                    # The previous solution subtracted link.end()-start-length
                    # from entities[x].offset. That's why the -1 multiplication.
                    shift_to = (link.end() - start - length) * -1
                    entities[x] = MessageEntity.shift_entities(shift_to, [entities[x]])[0]
            entities.append(MessageEntity('text_link', start, length, url=url))
            message = text_links.sub(r'\g<text>', message, count=1)
        for mention in mentions.finditer(message):
            entities.append(
                MessageEntity('mention',
                              mention.start(), mention.end() - mention.start(
                    )))
        for hashtag in hashtags.finditer(message):
            entities.append(
                MessageEntity('hashtag',
                              hashtag.start(), hashtag.end() - hashtag.start(
                    )))
        for botcommand in botcommands.finditer(message):
            entities.append(
                MessageEntity('bot_command',
                              botcommand.start(),
                              botcommand.end() - botcommand.start()))
        for url in urls.finditer(message):
            entities.append(
                MessageEntity('url', url.start(), url.end() - url.start()))

        return message, entities
