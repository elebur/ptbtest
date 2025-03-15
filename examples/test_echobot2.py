# ruff: noqa: PT009
import unittest

from telegram.ext import CommandHandler, MessageHandler, Updater, filters

from ptbtest import ChatGenerator, MessageGenerator, Mockbot, UserGenerator

"""
This is an example to show how the ptbtest suite can be used.
This example follows the echobot2 example at:
https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot2.py

"""


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

    def test_help(self):
        # this tests the help handler. So first insert the handler
        def help_message(update):
            update.message.reply_text("Help!")

        # Then register the handler with he updater's dispatcher and start polling
        self.updater.dispatcher.add_handler(CommandHandler("help", help_message))
        self.updater.start_polling()
        # We want to simulate a message. Since we don't care wich user sends it we let the MessageGenerator
        # create random ones
        update = self.mg.get_message(text="/help")
        # We insert the update with the bot so the updater can retrieve it.
        self.bot.insert_update(update)
        # sent_messages is the list with calls to the bot's outbound actions. Since we hope the message we inserted
        # only triggered one sendMessage action it's length should be 1.
        self.assertEqual(len(self.bot.sent_messages), 1)
        sent = self.bot.sent_messages[0]
        self.assertEqual(sent["method"], "sendMessage")
        self.assertEqual(sent["text"], "Help!")
        # Always stop the updater at the end of a testcase so it won't hang.
        self.updater.stop()

    def test_start(self):
        def start(update):
            update.message.reply_text("Hi!")

        self.updater.dispatcher.add_handler(CommandHandler("start", start))
        self.updater.start_polling()
        # Here you can see how we would handle having our own user and chat
        user = self.ug.get_user(first_name="Test", last_name="The Bot")
        chat = self.cg.get_chat(user=user)
        update = self.mg.get_message(user=user, chat=chat, text="/start")
        self.bot.insert_update(update)
        self.assertEqual(len(self.bot.sent_messages), 1)
        sent = self.bot.sent_messages[0]
        self.assertEqual(sent["method"], "sendMessage")
        self.assertEqual(sent["text"], "Hi!")
        self.updater.stop()

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


if __name__ == "__main__":
    unittest.main()
