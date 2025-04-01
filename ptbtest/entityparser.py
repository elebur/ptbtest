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
marked-up messages to plain text with entities.
Docs: https://core.telegram.org/bots/api#formatting-options
"""
import re
from typing import Tuple, Any, Sequence
from urllib.parse import urlparse

from telegram import MessageEntity

from ptbtest.errors import BadMarkupException


def get_utf_16_length(char: str) -> int:
    """
    Telegram uses UTF-16 for message entities:
    https://core.telegram.org/api/entities#utf-16

    A simple way of computing
    the entity length is converting the text to UTF-16,
    and then taking the byte length divided
    by 2 (=number of UTF-16 code units).
    Source: https://core.telegram.org/api/entities#computing-entity-length
    """
    return len(char.encode("utf-16-le")) // 2


def get_item(seq: Sequence, index: int, default: Any = None) -> Any:
    """
    Safely gets item from the sequence by its index.
    If the `index` is out of the range, then the default value is returned.
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


def check_and_normalize_url(url: str) -> str:
    if not url or url.startswith(" ") or url.endswith(" "):
        return ""

    result = url

    # If the protocol is not specified, setting 'http' protocol
    if "://" not in result:
        result = "http://" + result

    try:
        parse_url = urlparse(result)
    except ValueError:
        return ""

    if parse_url.scheme not in ("http", "https", "ton", "tg", "tonsite"):
        return ""

    # Adding trailing slash only for URLs without path. E.g.
    # https://www.example.com - adds the slash.
    # https://www.example.com/login - doesn't add the slash.
    if not parse_url.path and not result.endswith("/"):
        result += "/"

    return result


class EntityParser:
    @staticmethod
    def parse_markdown(text: str) -> Tuple[str, Tuple[MessageEntity, ...]]:
        """
        The method looks for Markdown V1 entities in the given text.
        Telegram documentation: https://core.telegram.org/bots/api#markdown-style
        Parameters:
            text (str): Message with a Markdown V1 text to be transformed

        Returns:
            (message, entities): The message as a plain text and entities found in the text.
        """
        entities = list()
        striped_text = text.strip()
        text_size = len(striped_text)
        utf16_offset = 0
        new_text = list()

        # https://github.com/TelegramMessenger/libprisma#supported-languages
        pre_code_language_pattern = re.compile(r"^([a-z0-9-]+)\s*")

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
                utf16_offset += get_utf_16_length(ch)
                new_text.append(ch)
                i += 1
                continue

            # Telegram returns error messages with the offset specified in bytes.
            # The length of strings and byte strings might be different. E.g.:
            # len('A©😊') == 3, while len('A©😊'.encode()) == 7.
            # This value is used only for the error message.
            begin_index_utf16 = len(striped_text[:i].encode())
            begin_index = i
            end_character = ch

            if ch == "[":
                end_character = "]"

            # Skipping the entity's opening char.
            i += 1
            language = ""

            is_pre = False
            if ch == "`" and i + 2 < text_size and striped_text[i:i+2] == "``":
                # The code entity has three chars (```).
                # The first one was skipped few lines above
                # (`i += 1` just above this `if`).
                # Increasing the counter by 2 to skip the rest of the entity's
                # symbols and jump to the text.
                i += 2
                is_pre = True
                # Trying to get language name.
                # E.g.:
                # ```python <- this name
                # print("Hello, world!")
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
                    if m := re.match(r"^]\s+\([^)]+\)", striped_text[i:]):
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

                utf16_offset += get_utf_16_length(entity_content)
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

                    if checked_url := check_and_normalize_url(url):
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

        return "".join(new_text).rstrip(), tuple(entities)


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
