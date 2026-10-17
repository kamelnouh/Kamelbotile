"""Telegram version of Kamelbotile.

Configure TELEGRAM_BOT_TOKEN and ADMIN_USER_ID in the environment before
starting the bot. The Telegram Bot API does not expose a personal Facebook
account session or other users' private contact details.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from bot_core import (
    HELP_TEXT,
    ChatStore,
    contains_facebook_link,
    format_bot_info,
    format_threads,
    is_admin_private_request,
)


def _admin_user_id() -> int | None:
    raw_value = os.getenv("ADMIN_USER_ID", "").strip()
    if not raw_value:
        return None
    try:
        return int(raw_value)
    except ValueError as error:
        raise SystemExit("ADMIN_USER_ID must be a numeric Telegram user ID.") from error


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "Missing TELEGRAM_BOT_TOKEN. Add it as a Replit Secret or environment variable."
        )

    # Import only at runtime so the command and storage logic stays independently testable.
    import telebot

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    bot = telebot.TeleBot(token)
    admin_user_id = _admin_user_id()
    database_path = os.getenv("BOT_DB_PATH", "bot_chats.sqlite3")
    chat_store = ChatStore(Path(database_path))

    def remember_message(message: object) -> None:
        chat = getattr(message, "chat", None)
        if chat is not None:
            chat_store.remember(chat)

    @bot.message_handler(commands=["start"])
    def start_command(message: object) -> None:
        remember_message(message)
        bot.reply_to(message, HELP_TEXT)

    @bot.message_handler(commands=["info"])
    def info_command(message: object) -> None:
        remember_message(message)
        try:
            bot.reply_to(message, format_bot_info(bot.get_me()))
        except Exception:
            # Avoid logging exception text that could include request URLs.
            logging.warning("Unable to retrieve the Telegram bot's own profile.")
            bot.reply_to(message, "ما قدرتش نجيب معلومات البوت الآن.")

    @bot.message_handler(commands=["threads"])
    def threads_command(message: object) -> None:
        remember_message(message)
        sender = getattr(message, "from_user", None)
        chat = getattr(message, "chat", None)
        sender_id = getattr(sender, "id", None)
        chat_type = getattr(chat, "type", None)

        if not is_admin_private_request(sender_id, chat_type, admin_user_id):
            bot.reply_to(message, "هذا الأمر متاح للمدير فقط وفي محادثة خاصة.")
            return

        bot.reply_to(message, format_threads(chat_store.recent(limit=10)))

    @bot.message_handler(
        func=lambda message: bool(getattr(message, "text", None))
        and contains_facebook_link(message.text)
    )
    def facebook_link_message(message: object) -> None:
        remember_message(message)
        bot.reply_to(
            message,
            "وصلني رابط Facebook. أقدر أتعرف على الرابط فقط، "
            "وما أستخرجش البريد أو رقم الهاتف أو معلومات خاصة.",
        )

    @bot.message_handler(func=lambda _message: True)
    def remember_other_message(message: object) -> None:
        remember_message(message)

    logging.info("Telegram bot is starting.")
    bot.infinity_polling(skip_pending=True, timeout=30)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
