# Testing requirements

## Static checks
- `python -m py_compile bot.py`
- Extract each inline JavaScript block and run `node --check` if Node is available.
- Parse HTML; check duplicate static IDs, unclosed markup, missing asset references.
- `python -m json.tool package.json`
- Inspect ZIP with `unzip -t`; ensure no `.env`, credentials, caches, node_modules, or virtualenv.

## Regression scenarios
1. Open Mini App from Telegram; invalid/missing initData is rejected.
2. Load feed; switch For You/Following quickly; no stale response overwrites newer mode.
3. Single tap pauses/plays; double tap toggles like exactly once without pausing; rapid taps reconcile with API.
4. Swipe exactly one item in feed, profile videos, search results and saved viewer.
5. Close a viewer and verify off-screen videos stop and resources are released.
6. Check `poster` for profile tiles, feed and saved viewer; test records with and without thumbnail.
7. Share a video and open the generated Telegram deep link from another Telegram account/device. Requires Main Mini App setup in BotFather.
8. Test slow network, API 4xx/5xx, offline/retry, empty feed, deleted/blocked videos.
9. Test upload limits, MIME/codec handling, ownership on delete, report flows, comment/follow/like persistence.
10. Test at least one small Android viewport and Telegram WebView, including keyboard and safe areas.

## Truthful reporting
Separate static tests, mocked API tests, staging tests, and real device/production tests. Passing one category does not imply passing the others.
