"""Fast static regression checks for Telegram Shorts' critical boot/comment flows."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "dist/index.html").read_text(encoding="utf-8")
BOT = (ROOT / "bot.py").read_text(encoding="utf-8")
SCHEMA = (ROOT / "database/schema.sql").read_text(encoding="utf-8")


class BootRegressionTests(unittest.TestCase):
    def test_auth_requests_have_bounded_timeouts(self):
        self.assertIn("api('/api/auth'", HTML)
        self.assertIn("},12000)", HTML)
        self.assertIn("api('/api/me'", HTML)

    def test_splash_has_timeout_recovery(self):
        self.assertIn("bootFailsafe=setTimeout", HTML)
        self.assertIn("retryBootFailsafe", HTML)
        self.assertIn("clearTimeout(bootFailsafe)", HTML)

    def test_inline_javascript_has_no_duplicate_dom_ids(self):
        ids = re.findall(r'\bid="([^\"]+)"', HTML.split("<script", 1)[0])
        self.assertEqual(len(ids), len(set(ids)))


class ThreadedCommentsTests(unittest.TestCase):
    def test_parent_id_is_migrated_in_runtime_and_schema(self):
        self.assertIn("alter table comments add column if not exists parent_id", BOT.lower())
        self.assertIn("parent_id bigint references comments(id) on delete cascade", SCHEMA.lower())

    def test_comment_api_validates_parent_belongs_to_video(self):
        self.assertIn('"select id, video_id, user_id from comments where id=$1 for update"', BOT)
        self.assertIn('int(parent["video_id"]) != video_id', BOT)

    def test_comment_api_returns_thread_parent(self):
        self.assertIn("return {\"ok\": True, \"comments\": [dict(row) for row in rows]}", BOT)
        self.assertIn("parent_id", BOT[BOT.index('@app.get("/api/videos/{video_id}/comments")'):BOT.index('@app.post("/api/users/{user_id}/follow")')])

    def test_frontend_has_reply_controls_and_sends_parent_id(self):
        self.assertIn("class=\"reply-comment\"", HTML)
        self.assertIn("JSON.stringify({text:t,...(parent?{parent_id:parent}:{})})", HTML)
        self.assertIn("resetReplyTarget", HTML)

    def test_comment_send_prevents_duplicate_submits(self):
        self.assertIn("btn.disabled=true;try{const r=await api('/api/videos/'+target+'/comments'", HTML)

    def test_comment_count_is_recomputed_from_database(self):
        section = BOT[BOT.index('@app.post("/api/videos/{video_id}/comments")'):BOT.index('@app.post("/api/users/{user_id}/follow")')]
        self.assertIn("select count(*) from comments where video_id=$1", section)
        self.assertIn("update videos set comments_count=$2 where id=$1", section)


if __name__ == "__main__":
    unittest.main()
