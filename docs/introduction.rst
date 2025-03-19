Introduction
============

**PTBtest** is test suite for developing ``python-telegram-bot`` driven Telegram bots. It lets you develop faster, since unit tests can be run without any dependency on contacting Telegram's servers.

Its features include:

- Mockbot: A fake bot that does not contact Telegram servers;
- Works with the updater from telegram.ext;
- Generator classes to easily create Users, Chats and Updates.

Installation
------------

PTBtest supports Python versions 3.9 and above. It's recommended to user a virtual environment to isolate your project's dependencies from other projects and the system. That said, you can install PTBtest with:

.. code:: shell
   $ pip install ptbtest --upgrade

Dependencies
~~~~~~~~~~~~

We strive for the least amount of dependencies, so, for now, PTBtest depends only on ``python-telegram-bot`` itself.
