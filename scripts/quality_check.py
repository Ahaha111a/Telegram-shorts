#!/usr/bin/env python3
"""Run offline-safe syntax, frontend, and unit checks for Telegram Shorts."""
from __future__ import annotations
import ast
import pathlib
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
FAILED = False


def run(name, command, cwd=ROOT):
    global FAILED
    print(f"\n== {name} ==")
    try:
        result = subprocess.run(command, cwd=cwd, text=True, check=False)
    except FileNotFoundError as exc:
        print(f"NOT RUN: {exc}")
        FAILED = True
        return
    print("PASS" if result.returncode == 0 else f"FAIL (exit {result.returncode})")
    if result.returncode:
        FAILED = True


print("== Python syntax ==")
for path in [ROOT / "bot.py", ROOT / "telegram_auth.py"]:
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        print(f"PASS: {path.relative_to(ROOT)}")
    except SyntaxError as exc:
        print(f"FAIL: {path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}")
        FAILED = True

print("\n== Production JavaScript syntax ==")
html = (ROOT / "dist/index.html").read_text(encoding="utf-8")
scripts = []
import re
for match in re.finditer(r"<script\b([^>]*)>(.*?)</script\s*>", html, re.I | re.S):
    attrs, body = match.group(1), match.group(2)
    if "src=" not in attrs.lower() and body.strip():
        scripts.append(body)
if not scripts:
    print("FAIL: no inline production script found")
    FAILED = True
else:
    for index, body in enumerate(scripts, 1):
        temp = ROOT / f".quality_inline_{index}.js"
        temp.write_text(body, encoding="utf-8")
        try:
            result = subprocess.run(["node", "--check", str(temp)], cwd=ROOT, text=True)
            if result.returncode:
                FAILED = True
                print(f"FAIL: inline script {index}")
            else:
                print(f"PASS: inline script {index}")
        except FileNotFoundError:
            FAILED = True
            print("NOT RUN: Node.js is not installed")
        finally:
            temp.unlink(missing_ok=True)

run("Telegram initData unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
print("\n== Archive structure checks ==")
required = ["bot.py", "telegram_auth.py", "dist/index.html", "database/schema.sql",
            "database/migrations/002_comment_social.sql", "database/migrations/003_storage_cleanup_queue.sql", "requirements.txt", ".env.example",
            "docs/PROJECT_GUIDE.md", "docs/QUALITY_CHECKLIST.md"]
for name in required:
    if (ROOT / name).is_file():
        print(f"PASS: {name}")
    else:
        print(f"FAIL: missing {name}")
        FAILED = True

print("\n== Backend integration availability ==")
try:
    import fastapi  # noqa
    import asyncpg  # noqa
    import aiogram  # noqa
    print("PASS: FastAPI, asyncpg and aiogram are importable")
except ImportError as exc:
    print(f"NOT RUN: backend integration tests need project dependencies ({exc})")
    # Local dependency availability is informational; no claim of API integration pass.

print("\nRESULT:", "FAIL" if FAILED else "PASS (offline checks only; live integrations are not exercised)")
sys.exit(1 if FAILED else 0)
