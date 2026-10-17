import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

import bot
from bot_core import (
    ChatStore,
    contains_facebook_link,
    format_bot_info,
    format_threads,
    is_admin_private_request,
)


class FacebookLinkTests(unittest.TestCase):
    def test_recognizes_supported_domains(self):
        for text in (
            "https://www.facebook.com/example",
            "m.facebook.com/example",
            "https://fb.com/example",
            "https://fb.watch/abc123",
        ):
            with self.subTest(text=text):
                self.assertTrue(contains_facebook_link(text))

    def test_rejects_lookalike_domain(self):
        self.assertFalse(contains_facebook_link("https://notfacebook.com/example"))
        self.assertFalse(contains_facebook_link(None))


class ChatStoreTests(unittest.TestCase):
    def test_remembers_and_updates_chat_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ChatStore(Path(directory) / "chats.sqlite3")
            chat = SimpleNamespace(
                id=123,
                type="private",
                first_name="Kamel",
                last_name="N",
                username="kamel",
                title=None,
            )

            store.remember(chat)
            chat.first_name = "Kamel Updated"
            store.remember(chat)

            rows = store.recent()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["chat_id"], 123)
            self.assertEqual(rows[0]["label"], "@kamel")
            self.assertEqual(rows[0]["chat_type"], "private")
            self.assertNotIn("message", rows[0])

    def test_thread_output_shows_only_chat_metadata(self):
        text = format_threads(
            [
                {
                    "label": "Family",
                    "chat_type": "group",
                    "chat_id": -12,
                    "last_seen": "not displayed",
                }
            ]
        )
        self.assertIn("Family", text)
        self.assertIn("-12", text)
        self.assertNotIn("not displayed", text)


class AccessAndInfoTests(unittest.TestCase):
    def test_threads_is_admin_only_and_private(self):
        self.assertTrue(is_admin_private_request(42, "private", 42))
        self.assertFalse(is_admin_private_request(7, "private", 42))
        self.assertFalse(is_admin_private_request(42, "group", 42))
        self.assertFalse(is_admin_private_request(42, "private", None))

    def test_bot_info_uses_own_public_telegram_fields(self):
        text = format_bot_info(
            SimpleNamespace(id=789, username="example_bot", first_name="Example")
        )
        self.assertIn("Example", text)
        self.assertIn("@example_bot", text)
        self.assertIn("789", text)
        self.assertNotIn("email", text.lower())
        self.assertNotIn("phone", text.lower())


class TelegramHandlerTests(unittest.TestCase):
    def test_commands_and_link_handler(self):
        instances = []

        class FakeTelegramBot:
            def __init__(self, token):
                self.token = token
                self.handlers = []
                self.replies = []
                instances.append(self)

            def message_handler(self, **filters):
                def register(handler):
                    self.handlers.append((filters, handler))
                    return handler

                return register

            def reply_to(self, message, text):
                self.replies.append((message, text))

            def get_me(self):
                return SimpleNamespace(
                    id=999,
                    username="test_bot",
                    first_name="Test Bot",
                )

            def infinity_polling(self, **_kwargs):
                return None

        class FakeTelebotModule:
            TeleBot = FakeTelegramBot

        def make_message(text, chat_type="private", sender_id=42):
            chat = SimpleNamespace(
                id=sender_id if chat_type == "private" else -100,
                type=chat_type,
                title="Test group" if chat_type != "private" else None,
                first_name="Admin" if chat_type == "private" else None,
                last_name=None,
                username="admin" if chat_type == "private" else None,
            )
            return SimpleNamespace(
                text=text,
                chat=chat,
                from_user=SimpleNamespace(id=sender_id),
            )

        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "TELEGRAM_BOT_TOKEN": "test-token",
                        "ADMIN_USER_ID": "42",
                        "BOT_DB_PATH": str(Path(directory) / "chats.sqlite3"),
                    },
                    clear=True,
                ),
                patch.dict("sys.modules", {"telebot": FakeTelebotModule}),
            ):
                bot.main()

            fake_bot = instances[0]
            start_handler = next(
                handler
                for filters, handler in fake_bot.handlers
                if filters.get("commands") == ["start"]
            )
            info_handler = next(
                handler
                for filters, handler in fake_bot.handlers
                if filters.get("commands") == ["info"]
            )
            threads_handler = next(
                handler
                for filters, handler in fake_bot.handlers
                if filters.get("commands") == ["threads"]
            )
            link_handler = next(
                handler
                for filters, handler in fake_bot.handlers
                if "func" in filters
                and filters["func"](make_message("https://fb.watch/a"))
            )

            start_message = make_message("/start")
            start_handler(start_message)
            self.assertIn("/threads", fake_bot.replies[-1][1])

            info_handler(make_message("/info"))
            self.assertIn("@test_bot", fake_bot.replies[-1][1])

            threads_handler(make_message("/threads"))
            self.assertIn("admin", fake_bot.replies[-1][1])

            link_handler(make_message("https://fb.watch/a"))
            self.assertIn("ما أستخرجش", fake_bot.replies[-1][1])


if __name__ == "__main__":
    unittest.main()
