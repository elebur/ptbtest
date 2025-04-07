import re

ERR_MSG_CANT_PARSE = re.escape("Can't parse entities: can't find end "
                               "of the entity starting at byte offset")
# Do it this way to prevent escaping of '{}' symbols.
ERR_MSG_CANT_PARSE += " {offset}"

ERR_MSG_EMPTY_STR = re.escape("Text must be non-empty")

MARKDOWN_V2_RESERVED_CHARS = "_*[]()~`>#+-=|{}.!"
