# Technical audit — 2026-10-16

## Source verification
The supplied ZIP has 12 archive entries and passed `ZipFile.testzip()`. Its Git blob SHA matched the GitHub `main` content for `dist/index.html`, `bot.py`, `README.md`, `package.json`, `requirements.txt`, and `database/schema.sql`. This confirms these files were in sync at audit time; GitHub writes/deployment were not performed. The ZIP initially lacked `docs/quality` and `.env.example`.

## Confirmed findings
- P1 UI: `.shade` applied a black gradient down to `#000d` at the bottom of every feed slide. `.vignette` added `inset 0 0 120px #0008`. The bottom navigation added a gradient and `box-shadow` above the panel. These are direct code causes for visible lower darkening.
- P1 sharing: `shareCurrent` used `location.origin+'/?video='+v.id`, a normal web URL, not a Telegram Mini App deep link. New backend route returns `https://t.me/<bot>?startapp=video_<id>`; this depends on BotFather configuration and must be tested in Telegram. Frontend reads the Telegram `start_param` payload `video_ID` and attempts to fetch/open that video in the vertical viewer. This still depends on Main Mini App configuration and requires real Telegram testing.
- P1 gestures: feed attached both `dblclick` and touch `pointerup` handlers, potentially issuing two toggles for one double tap. Current patch suppresses synthetic dblclick action, delays single-tap playback to distinguish it from a double tap, and adds the same double-tap like behavior to the saved/profile/search viewer. Real-device test remains required.
- P1 swipe: saved viewer used viewport-sized items inside a panel whose CSS height could be only 90dvh; offsets used `window.innerHeight`. The viewer panel/items were aligned to full viewport height to prevent snap geometry mismatch.
- P1 thumbnails: DB schema contains `thumbnail_url`, but frontend had no `thumbnail_url` usage or `poster` attribute. SQL projections and frontend rendering now carry/use the field. The upload path does not yet demonstrate automatic thumbnail generation; legacy videos may remain without poster.
- P1 release confidence: `package.json` build script only prints a message and is not a real frontend build. Static checks do not validate production integrations.
- P2 architecture: production frontend is a large single HTML file; `src/main.jsx` and `src/style.css` are minimal placeholders. This increases regression risk and makes duplicate CSS overrides harder to track. Do not migrate framework during this critical-fix pass.
- P2 product: backend/schema include watch-history endpoints/tables although the product requirement says no history UI. Keep existing DB schema for compatibility, but remove/disable UI entry points and do not delete stored data without approval.
- P2 API coverage: routes exist for feed, profile, search, notifications, likes, saves, comments, follows, reports, upload and deletion. Presence of a route is not proof of end-to-end correctness.

## Function status (static inspection only)
| Function | Status | Evidence/next validation |
|---|---|---|
| Telegram auth | Implemented; requires tests | Test valid, expired, malformed initData |
| Feed / Following | Implemented; needs runtime tests | race conditions, empty/error states |
| Video playback | Implemented; needs device test | autoplay, lifecycle, memory/network |
| Like button / double tap | Known risk patched; needs Android test | exactly one request, state/count sync |
| Comments | Route/UI present; needs runtime test | create, load, delete, error states |
| Profiles | Route/UI present; partial | thumbnails depend on DB values |
| Follow/unfollow | Route/UI present; needs runtime test | persistence and counts |
| Upload/delete | Route/UI present; needs integration test | storage cleanup, limits, ownership |
| Search | Route/UI present; needs runtime test | users/videos/hashtags and empty state |
| Notifications | Route/UI present; needs runtime test | unread count/read persistence |
| Saved videos | Route/UI present; viewer snap patched | real swipe and actions on device |
| Reports/moderation | Route/UI present; needs runtime test | reason validation and admin permissions |
| Share Mini App link | Changed; partial | Main Mini App setup and start-param routing need verification |
| Video poster | Code now passes field; partial | thumbnail generation/storage not confirmed |
| History UI | Requirement says absent; legacy backend exists | verify no UI entry point after full review |

## Not performed
No live Android/Telegram WebView test, Railway deployment/log inspection, Supabase live DB/Storage test, security penetration test, load test or real video upload was performed.

## Recommended order
1. Verify v15 code in Telegram Android: bottom darkening, one-swipe behavior, double tap and deep link.
2. Implement and test `start_param` handling to open `video_ID` directly in the Mini App.
3. Generate thumbnails on upload (server-side ffmpeg or trusted thumbnail service; assess Railway availability/cost first).
4. Add API integration tests for auth, ownership, idempotency and storage cleanup.
5. Add frontend automated tests and break up the single HTML only after the core stabilizes.
6. Remove all history UI references while preserving schema until migration approved.
