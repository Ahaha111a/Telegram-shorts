# Telegram Shorts — Stable Social v4

Production-ready Telegram Mini App + bot for a vertical short-video feed.

## Production

Railway runs the backend with:

```bash
python bot.py
```

The production Mini App is served directly from `dist/index.html` by the FastAPI app.

## Included

- Telegram WebApp authentication with server-side validation
- Smooth vertical video feed with autoplay/pause and scroll-snap
- Recommended / Following switch with stale-request protection
- Likes, saves, comments, follows and view tracking
- Saved videos and watch history with vertical viewer
- Profile, followers/following and profile editing
- Search for users, hashtags and videos
- Notifications
- Reports and moderation endpoints
- Persistent "Not interested" and "Don't show this author"
- User blocking and user reports
- Automatic database/storage initialization
- `.env.example` included

## Environment

Use `.env.example` as the template for local configuration. Never commit real secrets.

Required Railway variables:

- `BOT_TOKEN`
- `DATABASE_URL`
- `WEB_APP_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ADMIN_TELEGRAM_IDS`

## Important

Do not replace `dist/index.html` with a separate React/Vite build. The current production UI is the tested static Mini App shipped with this archive.


### UX policy
- История просмотров отключена и больше не записывается приложением.
- Лайк не должен менять состояние воспроизведения видео.
- Счётчики профиля используют фиксированную адаптивную сетку.
