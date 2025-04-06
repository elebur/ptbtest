import asyncio

from telegram import Chat, User, MessageEntity
from telegram.constants import ChatType, MessageEntityType

from main import build_app
from mock_application import MockApplication
from ptbtest import MessageGenerator


async def main():
    # Building the application, configuring all handlers.
    app = build_app("asdfasdf")
    mock_app = MockApplication(app, "TestBot", "test_bot", 777)
    async with mock_app:
        chat_id = 777
        # "Sending" a message
        mock_app.send_private_message("Hello, PTBTest!", 777)

        # Checks that there is only one pending update.
        assert len(mock_app.incoming_updates) == 1

        # Forcing the application to process all updates.
        await mock_app.process_updates()
        # Checking that the bot sent exactly one message.
        assert len(mock_app.sent_messages) == 1

        print("sent messages".center(80, "-"))
        print(mock_app.last_sent_message)

        assert mock_app.last_sent_message.from_user.username == "test_bot"
        assert mock_app.last_sent_message.chat.id == 777
        assert mock_app.last_sent_message.text == f"Your message is 'Hello, PTBTest!'"

        mock_app.clear_sent_messages()

        print("\n\n", "the second text".center(120, "="), "\n\n")

        command_msg = MessageGenerator(mock_app._bot).get_message(
            chat=Chat(first_name='test_user', id=123, type=ChatType.PRIVATE, username='test_user'),
            # date=datetime.datetime(2025, 4, 3, 16, 24, 50, tzinfo=datetime.timezone.utc),
            entities=(MessageEntity(length=5, offset=0, type=MessageEntityType.BOT_COMMAND),),
            user=User(first_name='test_user', id=123, is_bot=False, language_code='en', username='test_user'),
            text="/help"
        )

        mock_app.add_update(command_msg)
        await mock_app.process_updates()

        assert len(mock_app.sent_messages) == 1

        print("sent messages".center(80, "-"))
        print(mock_app.last_sent_message)
        assert mock_app.last_sent_message.message_id == 2
        assert mock_app.last_sent_message.text == "Help!"

asyncio.get_event_loop().run_until_complete(main())