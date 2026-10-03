# Telegram Shorts — Stable Social v10

Production Telegram Mini App + bot for a TikTok/Reels-style vertical short-video feed.

## Production
Railway start command:
```bash
python bot.py
```
The production Mini App is served from `dist/index.html`.

## v7 focus
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
