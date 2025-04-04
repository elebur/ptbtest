import asyncio

from telegram import Chat, User
from telegram.constants import ChatType

from main import build_app
from ptbtest import MessageGenerator
from utils import UpdateFeeder, process_updates
from utils import patch_app


async def main():
    # Building the application, configuring all handlers.
    app = build_app("asdfasdf")
    # Replacing original objects with mocked ones.
    app, mock_api = patch_app(app, "AlphaBeta", "alpha_beta", 777)
    async with app:
        # Creating an object, that will help us to put messages
        # into the updates queue.
        udpate_feeder = UpdateFeeder(app.bot, mock_api)

        # The message that will be sent.
        regular_msg = MessageGenerator(app.bot).get_message(
            chat=Chat(first_name='test_user', id=123, type=ChatType.PRIVATE, username='test_user'),
            user=User(first_name='test_user', id=123, is_bot=False, language_code='en', username='test_user'),
            text="start",
        )

        # Put the message into the queue.
        udpate_feeder.add_update(regular_msg)
        # Checks that there is only one pending update.
        assert len(mock_api._incoming_updates) == 1

        # Forcing the application to process all updates.
        await process_updates(app, udpate_feeder)

        # Checking that the bot sent exactly one message.
        assert len(mock_api.sent_messages) == 1

        msg = mock_api.sent_messages[-1]
        print("sent messages".center(80, "-"))
        print(mock_api.last_message)

        assert msg.from_user.username == "alpha_beta"
        assert msg.chat.id == 123

        mock_api.clear_sent_messages()

        print("\n\n", "the second text".center(120, "="), "\n\n")

        command_msg = MessageGenerator(app.bot).get_message(
            chat=Chat(first_name='test_user', id=123, type=ChatType.PRIVATE, username='test_user'),
            # date=datetime.datetime(2025, 4, 3, 16, 24, 50, tzinfo=datetime.timezone.utc),
            # entities=(MessageEntity(length=5, offset=0, type=MessageEntityType.BOT_COMMAND),),
            user=User(first_name='test_user', id=123, is_bot=False, language_code='en', username='test_user'),
            text="help"
        )

        udpate_feeder.add_update(command_msg)
        assert len(mock_api._incoming_updates) == 1

        await process_updates(app, udpate_feeder)

        assert len(mock_api.sent_messages) == 1

        print("sent messages".center(80, "-"))
        print(mock_api.last_message)
        assert mock_api.last_message.message_id == 2
        assert mock_api.last_message.text == "I will help you!"

asyncio.get_event_loop().run_until_complete(main())