# PTBtest
> A test suite for [Python Telegram Bot](https://github.com/python-telegram-bot/python-telegram-bot/).

> **This application is NOT in an usable state yet!**

This library is meant for people wanting to write unit tests for their python-telegram-bot driven bots.

![](header.png)

## Installation

OS X & Linux:

```bash
$ pip install ptbtest
```

Windows:

```sh
pip install ptbtest
```

## Usage example

The following things make this library attractive to create unit tests:

* Mockbot - A fake bot that does not contact telegram servers;
* Works with the updater from telegram.ext;
* Generator classes to easily create Users, Chats and Updates.

The example below is based on the echobot2 example at:
https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot2.py

It uses unittest\'s style but can be easily translated to pytest\'s.

```python
import unittest

class TestEchobot2(unittest.TestCase):
    def setUp(self):

        # For use within the tests we nee some stuff. Starting with a Mockbot
        self.bot = Mockbot()

        # Some generators for users and chats
        self.ug = UserGenerator()
        self.cg = ChatGenerator()

        # And a Messagegenerator and updater (for use with the bot.)
        self.mg = MessageGenerator(self.bot)
        self.updater = Updater(bot=self.bot)

    def test_echo(self):

        def echo(update):
            update.message.reply_text(update.message.text)

        self.updater.dispatcher.add_handler(MessageHandler(filters.text, echo))
        self.updater.start_polling()

        update = self.mg.get_message(text="first message")
        update2 = self.mg.get_message(text="second message")

        self.bot.insert_update(update)
        self.bot.insert_update(update2)

        self.assertEqual(len(self.bot.sent_messages), 2)

        sent = self.bot.sent_messages

        self.assertEqual(sent[0]["method"], "sendMessage")
        self.assertEqual(sent[0]["text"], "first message")
        self.assertEqual(sent[1]["text"], "second message")

        self.updater.stop()
```

_For more examples and usage, please refer to the [documentation](http://ptbtestsuite.readthedocs.io/en/master/?badge=master)_.

## Development setup

### Dependencies

- Hatch

To install the package for development, clone the repository and:

```bash
hatch init
```

To run the tests:

```bash
hatch test
```
