# ruff: noqa: PT009
import unittest

from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, RegexHandler, Updater, filters

from ptbtest import ChatGenerator, MessageGenerator, Mockbot, UserGenerator

"""
This is an example to show how the ptbtest suite can be used.
This example follows the conversationbot2 example at:
https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/conversationbot2.py

"""


class TestConversationbot2(unittest.TestCase):
    def setUp(self):
        self.bot = Mockbot()
        self.cg = ChatGenerator()
        self.ug = UserGenerator()
        self.mg = MessageGenerator(self.bot)
        self.updater = Updater(bot=self.bot)

    def test_conversation(self):
        choosing, typing_reply, typing_choice = range(3)

        reply_keyboard = [["Age", "Favourite colour"], ["Number of siblings", "Something else..."], ["Done"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

        def facts_to_str(user_data):
            facts = []
            for key, value in user_data.items():
                facts.append(f"{key} - {value}")

            return "\n".join(facts).join(["\n", "\n"])

        def start(update):
            update.message.reply_text(
                "Hi! My name is Doctor Botter. I will hold a more complex conversation with you. "
                "Why don't you tell me something about yourself?",
                reply_markup=markup,
            )

            return choosing

        def regular_choice(update, user_data):
            text = update.message.text
            user_data["choice"] = text
            update.message.reply_text(f"Your {text.lower()}? Yes, I would love to hear about that!")

            return typing_reply

        def custom_choice(update):
            update.message.reply_text(
                "Alright, please send me the category first, " 'for example "Most impressive skill"'
            )

            return typing_choice

        def received_information(update, user_data):
            text = update.message.text
            category = user_data["choice"]
            user_data[category] = text
            del user_data["choice"]

            update.message.reply_text(
                f"Neat! Just so you know, this is what you already told me:"
                f"{facts_to_str(user_data)}"
                f"You can tell me more, or change your opinion on something.",
                reply_markup=markup,
            )

            return choosing

        def done(update, user_data):
            if "choice" in user_data:
                del user_data["choice"]

            update.message.reply_text(
                f"I learned these facts about you:" f"{facts_to_str(user_data)}" f"Until next time!"
            )

            user_data.clear()
            return ConversationHandler.END

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                choosing: [
                    RegexHandler("^(Age|Favourite colour|Number of siblings)$", regular_choice, pass_user_data=True),
                    RegexHandler("^Something else...$", custom_choice),
                ],
                typing_choice: [
                    MessageHandler(filters.text, regular_choice, pass_user_data=True),
                ],
                typing_reply: [
                    MessageHandler(filters.text, received_information, pass_user_data=True),
                ],
            },
            fallbacks=[RegexHandler("^Done$", done, pass_user_data=True)],
        )
        dp = self.updater.dispatcher
        dp.add_handler(conv_handler)
        self.updater.start_polling()

        # We are going to test a conversationhandler. Since this is tied in with user and chat we need to
        # create both for consistancy
        user = self.ug.get_user()
        chat = self.cg.get_chat(type="group")
        user2 = self.ug.get_user()
        chat2 = self.cg.get_chat(user=user)

        # let's start the conversation
        u = self.mg.get_message(user=user, chat=chat, text="/start")
        self.bot.insert_update(u)
        data = self.bot.sent_messages[-1]
        self.assertRegex(data["text"], r"Doctor Botter\. I will")
        u = self.mg.get_message(user=user, chat=chat, text="Age")
        self.bot.insert_update(u)
        data = self.bot.sent_messages[-1]
        self.assertRegex(data["text"], r"Your age\? Yes")

        # now let's see what happens when another user in another chat starts conversating with the bot
        u = self.mg.get_message(user=user2, chat=chat2, text="/start")
        self.bot.insert_update(u)
        data = self.bot.sent_messages[-1]
        self.assertRegex(data["text"], r"Doctor Botter\. I will")
        self.assertEqual(data["chat_id"], chat2.id)
        self.assertNotEqual(data["chat_id"], chat.id)
        # and cancels his conv.
        u = self.mg.get_message(user=user2, chat=chat2, text="Done")
        self.bot.insert_update(u)
        data = self.bot.sent_messages[-1]
        self.assertRegex(data["text"], r"Until next time!")

        # cary on with first user
        u = self.mg.get_message(user=user, chat=chat, text="23")
        self.bot.insert_update(u)
        data = self.bot.sent_messages[-1]
        self.assertRegex(data["text"], r"Age - 23")
        u = self.mg.get_message(user=user, chat=chat, text="Something else...")
        self.bot.insert_update(u)
        data = self.bot.sent_messages[-1]
        self.assertRegex(data["text"], r"Most impressive skill")
        u = self.mg.get_message(user=user, chat=chat, text="programming skill")
        self.bot.insert_update(u)
        data = self.bot.sent_messages[-1]
        self.assertRegex(data["text"], r"Your programming skill\? Yes")
        u = self.mg.get_message(user=user, chat=chat, text="High")
        self.bot.insert_update(u)
        data = self.bot.sent_messages[-1]
        self.assertRegex(data["text"], r"programming skill - High")
        u = self.mg.get_message(user=user, chat=chat, text="Done")
        self.bot.insert_update(u)
        data = self.bot.sent_messages[-1]
        self.assertRegex(data["text"], r"programming skill - High")
        self.assertRegex(data["text"], r"Age - 23")

        self.updater.stop()


if __name__ == "__main__":
    unittest.main()
