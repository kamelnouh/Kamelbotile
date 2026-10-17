# Kamelbotile — Python Telegram edition

This version runs as a Telegram bot. The existing JavaScript files are retained
in the repository as a reference; the Replit run command starts `bot.py`.

## Commands

- `/start` shows the help message.
- `/info` shows the bot's own Telegram name, username, and ID.
- `/threads` lists up to 10 chats that have already contacted the bot. It works
  only for the configured admin, in a private chat with the bot.
- Facebook links are detected, but the bot does not fetch private profile,
  email, or phone information.

The bot stores only chat IDs, chat type, a display label, and last-seen time in
`bot_chats.sqlite3`. It does not store message bodies. Restrict access to the
Replit project and its files because this metadata can still identify chats.

## Run on Replit

1. Add `TELEGRAM_BOT_TOKEN` as a Replit Secret.
2. Set `ADMIN_USER_ID` to the numeric Telegram user ID allowed to use `/threads`.
   Leave it unset to disable that command for everyone.
3. Run the project. Its configured command is `python bot.py`.

`BOT_DB_PATH` can optionally point to a different SQLite database file.

## Tests

Run `python -m unittest discover -s tests`.

## Existing Facebook session file

The legacy repository contains a tracked `appstate.json`. This Python Telegram
version does not read it. Because the file is public and the legacy code uses
it for cookie-based login, treat any active session values in it as exposed:
revoke those Facebook sessions and remove the file from the repository history.
Adding it to `.gitignore` alone does not remove a file already tracked by Git.
