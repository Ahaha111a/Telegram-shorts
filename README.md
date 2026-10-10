# Telegram Shorts — Stable Social v12

Production Telegram Mini App + bot for a TikTok/Reels-style vertical short-video feed.

## Production
Railway start command:
```bash
python bot.py
```
The production Mini App is served from `dist/index.html`.

## v12 fixes and improvements
- Removed the bottom navigation element, styles, event delegation, and reserved vertical space completely.
- Moved Search, Create, Notifications, and Profile into compact top-bar actions; unread notification badge remains available.
- Hardened Telegram initData validation: duplicate query parameters, missing/malformed auth_date, future timestamps, expired signatures, and invalid user IDs are rejected.

## v11 fixes and improvements
- `/api/me` now returns the current user’s published videos, fixing the empty profile tab.
- Comment likes with per-user uniqueness, live counts, and migration on startup.
- Nested comments/replies use a clearer threaded visual treatment.
- Comment deletion confirms first and recalculates the video comment count from the actual remaining rows.
- The alternate video viewer now includes like/comment/follow/share/save/more actions for search, profile, and saved videos.
- Removed the dark scrim from the bottom navigation; the panel itself remained in v11 and is fully removed in v12.
- Destructive confirmations use Telegram WebApp confirmation UI when available.

## Previous UI foundation
- UI Foundation rebuilt around one consistent spacing/typography/icon system
- TikTok/Reels-inspired feed interaction model
- Like/save/follow actions are isolated from video playback
- Optimistic like UI with rollback on network failure
- Stable panel stack + Telegram Back + backdrop + safe-area handling
- Top-bar navigation remains available when no blocking panel is open
- Profile statistics use fixed tabular numeric layout
- Watch-history UI and watch-history storage are not used by the app
- Missing moderation/preference tables are created automatically at startup
- Production errors return a safe JSON response instead of raw internal details

## Railway variables
- `BOT_TOKEN`
- `DATABASE_URL`
- `WEB_APP_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ADMIN_TELEGRAM_IDS`

`.env.example` is optional for GitHub and is intentionally not required for production.


## v10 focus
- Deterministic mobile video gestures: tap pause/play, double-tap like.
- High-contrast bottom navigation.
- Profile/Saved tab navigation and nested social navigation.
- Watch history remains removed.

- В v10 добавлены ответы на комментарии, атомарный лайк и уведомления о лайках/ответах.


## QA performed for v12
- Python syntax compilation checked locally.
- Inline JavaScript syntax checked locally with Node.js.
- Verified the bottom navigation markup and delegated handlers are removed and top-bar action handlers remain wired.
- Verified initData rejects duplicate parameters, missing/invalid/future/expired auth_date values and invalid user IDs.
- Real Telegram/Railway/Supabase runtime tests were not performed; deploy and verify against connected services before announcing production readiness.
