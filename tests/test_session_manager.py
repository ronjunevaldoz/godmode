import json
import tempfile
import unittest
from pathlib import Path
from memory.session_manager import SessionManager


class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.sm = SessionManager(sessions_dir=self.tmp)

    def test_load_empty_for_new_session(self):
        self.assertEqual(self.sm.load("new"), [])

    def test_append_and_load_roundtrip(self):
        self.sm.append("s1", "user", "hello")
        self.sm.append("s1", "assistant", "hi there")
        history = self.sm.load("s1")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["content"], "hi there")

    def test_turn_count(self):
        for i in range(3):
            self.sm.append("s1", "user", f"msg {i}")
            self.sm.append("s1", "assistant", f"resp {i}")
        self.assertEqual(self.sm.turn_count("s1"), 3)

    def test_list_sessions(self):
        self.sm.append("alpha", "user", "x")
        self.sm.append("beta", "user", "y")
        self.assertIn("alpha", self.sm.list_sessions())
        self.assertIn("beta", self.sm.list_sessions())

    def test_clear_removes_session(self):
        self.sm.append("s1", "user", "hi")
        self.assertTrue(self.sm.clear("s1"))
        self.assertEqual(self.sm.load("s1"), [])

    def test_clear_nonexistent_returns_false(self):
        self.assertFalse(self.sm.clear("ghost"))

    def test_truncate_keeps_recent_within_budget(self):
        big = "x" * 3000
        messages = [{"role": "user", "content": big} for _ in range(5)]
        kept = self.sm.truncate_to_budget(messages)
        total_chars = sum(len(m["content"]) for m in kept)
        self.assertLessEqual(total_chars, 8000)
        self.assertGreater(len(kept), 0)

    def test_truncate_keeps_all_if_within_budget(self):
        messages = [{"role": "user", "content": "short"} for _ in range(4)]
        kept = self.sm.truncate_to_budget(messages)
        self.assertEqual(len(kept), 4)

    def test_corrupted_file_returns_empty(self):
        p = Path(self.tmp) / "bad.json"
        p.write_text("not json{{")
        self.assertEqual(self.sm.load("bad"), [])
