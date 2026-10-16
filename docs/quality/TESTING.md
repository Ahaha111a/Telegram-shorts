# Testing and regression protocol

## Every change

1. Run `python -m py_compile bot.py`.
2. Extract inline scripts from `dist/index.html` and run `node --check` on each extracted script.
3. Run `python -m unittest discover -s tests -v`.
4. Validate `database/schema.sql` with a PostgreSQL parser or a disposable test database when available.
5. Inspect the diff and confirm no secrets, `.env`, cache, or generated dependencies entered the patch.

## Critical manual scenarios

- Telegram Android: launch Mini App, open profile/search/saved/notifications; each should fill the available viewport and close back to the prior context.
- Feed: one tap performs only the configured playback action; double tap toggles like exactly once; button tap is independent; no pause caused by double tap.
- Rapid likes: repeat desired-state requests and confirm UI/DB agree after the last response.
- Comments: reject whitespace-only text; add once; delete own comment only after confirmation; cancel leaves it unchanged; errors do not create optimistic false counters.
- Video delete: cancel leaves video; confirm soft-deletes only owner content; failure preserves list/counter truth.
- Scroll: rapid swipes in feed, profile viewer and saved viewer; one active video at a time; returning to a tab should not start multiple videos.
- Share: share URL must be `t.me/<bot>?startapp=video_ID`; opening in Telegram should resolve `start_param` and load that video.
- Poster: check videos with and without `thumbnail_url`.
- Network: throttled connection, API timeout, malformed response, retry and app resume.

## Current automated checks

`tests/test_quality_regressions.py` is a static source-level suite. It does not prove visual correctness or server integration. Run it locally before release. No real Telegram Android or production DB test is claimed by the source archive alone.
