# ROADMAP

## Structure

### telegram.ext

- Mockbot
- ApplicationBuilder
- Updater
- BaseHandler
    - CommandHandler
    - MessageHandler
- ContextTypes
    - CallBackContext
- filters

## Mockbot

- In PTB, Bot is a context manager (async with). Mockbot should be also.
- A Bot can't initiate a conversation. Mockbot shouldn't also.

