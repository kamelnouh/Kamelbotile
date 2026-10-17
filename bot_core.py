"""Small, testable pieces of the Telegram bot."""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HELP_TEXT = (
    "🤖 مرحباً! أنا بوت Telegram.\n\n"
    "الأوامر:\n"
    "/start — عرض المساعدة\n"
    "/info — معلومات حساب البوت\n"
    "/threads — آخر المحادثات التي تواصلت مع البوت (للمدير فقط)\n\n"
    "يمكنني ملاحظة روابط Facebook، لكن لا أستخرج البريد أو رقم الهاتف "
    "أو البيانات الخاصة من الحسابات."
)

_FACEBOOK_LINK_RE = re.compile(
    r"(?i)(?<![\w.-])(?:(?:https?://)?(?:www\.|m\.)?)?"
    r"(?:facebook\.com|fb\.com|fb\.watch)(?=[:/?#\s]|$)"
)


def contains_facebook_link(text: str | None) -> bool:
    """Return whether text mentions a supported Facebook URL/domain."""
    return bool(text and _FACEBOOK_LINK_RE.search(text))


def chat_label(chat: Any) -> str:
    """Choose a readable label without storing message content."""
    title = getattr(chat, "title", None)
    if title:
        return str(title)

    username = getattr(chat, "username", None)
    if username:
        return f"@{username}"

    first_name = getattr(chat, "first_name", None) or ""
    last_name = getattr(chat, "last_name", None) or ""
    full_name = f"{first_name} {last_name}".strip()
    return full_name or "محادثة خاصة"


class ChatStore:
    """Persist only chat metadata needed by /threads; never message bodies."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY,
                    chat_type TEXT NOT NULL,
                    label TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                )
                """
            )

    def remember(self, chat: Any) -> None:
        chat_id = int(chat.id)
        chat_type = str(getattr(chat, "type", "unknown"))
        label = chat_label(chat)
        last_seen = datetime.now(timezone.utc).isoformat(timespec="seconds")

        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO chats (chat_id, chat_type, label, last_seen)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    chat_type = excluded.chat_type,
                    label = excluded.label,
                    last_seen = excluded.last_seen
                """,
                (chat_id, chat_type, label, last_seen),
            )

    def recent(self, limit: int = 10) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 50))
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT chat_id, chat_type, label, last_seen
                FROM chats
                ORDER BY last_seen DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [dict(row) for row in rows]


def is_admin_private_request(
    user_id: int | None, chat_type: str | None, admin_user_id: int | None
) -> bool:
    """Keep /threads private and restricted to the configured bot owner."""
    return (
        user_id is not None
        and admin_user_id is not None
        and int(user_id) == int(admin_user_id)
        and chat_type == "private"
    )


def format_bot_info(bot_user: Any) -> str:
    """Format non-sensitive information about the bot's own Telegram account."""
    username = getattr(bot_user, "username", None)
    username_line = f"👤 اسم المستخدم: @{username}\n" if username else ""
    return (
        "ℹ️ معلومات حساب البوت:\n"
        f"الاسم: {getattr(bot_user, 'first_name', 'غير متاح')}\n"
        f"{username_line}"
        f"المعرّف: {getattr(bot_user, 'id', 'غير متاح')}"
    )


def format_threads(chats: list[dict[str, Any]]) -> str:
    if not chats:
        return "ما زالت ما كاين حتى محادثة مسجلة."

    lines = ["📂 آخر المحادثات التي تواصلت مع البوت:"]
    for index, chat in enumerate(chats, start=1):
        lines.append(
            f"{index}. {chat['label']} "
            f"(النوع: {chat['chat_type']}، المعرّف: {chat['chat_id']})"
        )
    return "\n".join(lines)
