# Telegram Shorts — Stable Social v11

Production Telegram Mini App + bot for a TikTok/Reels-style vertical short-video feed.

## Production
Railway start command:
```bash
python bot.py
```
The production Mini App is served from `dist/index.html`.

## v11 fixes and improvements
- `/api/me` now returns the current user’s published videos, fixing the empty profile tab.
- Comment likes with per-user uniqueness, live counts, and migration on startup.
- Nested comments/replies use a clearer threaded visual treatment.
- Comment deletion confirms first and recalculates the video comment count from the actual remaining rows.
- The alternate video viewer now includes like/comment/follow/share/save/more actions for search, profile, and saved videos.
- Bottom navigation no longer draws a dark gradient/blur scrim over the video.
- Destructive confirmations use Telegram WebApp confirmation UI when available.

## Previous UI foundation
- UI Foundation rebuilt around one consistent spacing/typography/icon system
- TikTok/Reels-inspired feed interaction model
- Like/save/follow actions are isolated from video playback
- Optimistic like UI with rollback on network failure
- Stable panel stack + Telegram Back + backdrop + safe-area handling
- Bottom navigation hides while panels are open
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


## QA performed for v11
- Python syntax parsed successfully.
- Inline JavaScript passed `node --check`.
- Checked that the profile API now returns published videos, and that comment-like routes/table are present.
- Checked frontend action wiring and exact comment-count responses.
- Real Telegram/Railway/Supabase runtime tests were not possible in this local review; deploy and verify against the connected services before announcing production readiness.
