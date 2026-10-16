# Release checklist

- [ ] ZIP and GitHub `main` have been compared by Git blob SHA.
- [ ] No secret values or `.env` included; `.env.example` contains placeholders only.
- [ ] Python compile and JS syntax checks pass.
- [ ] HTML/package/SQL files reviewed; ZIP integrity verified.
- [ ] API auth, ownership checks, error paths and rate limits reviewed.
- [ ] Feed, following, gestures, likes, comments, saves, profiles, upload, delete, search and reports tested.
- [ ] Thumbnails tested for populated and empty `thumbnail_url`.
- [ ] Telegram share link tested with Main Mini App configured.
- [ ] Bottom gradient checked in actual Telegram Android WebView at top, middle and bottom of video.
- [ ] Railway deployment commit and logs checked after deploy.
- [ ] Supabase connectivity and Storage bucket verified without exposing secrets.
- [ ] Remaining untested scenarios disclosed to user.
