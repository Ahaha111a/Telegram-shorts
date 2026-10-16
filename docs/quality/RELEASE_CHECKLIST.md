# Release checklist

## Source and configuration
- [ ] Confirm ZIP and GitHub `main` source identity; review differences before replacing files.
- [ ] Check all required environment variables in Railway without printing values.
- [ ] Keep `.env` and secrets out of Git; `.env.example` contains names only.
- [ ] Review dependencies and production start command.

## Automated checks
- [ ] `python -m py_compile bot.py`
- [ ] JavaScript syntax checks for inline scripts.
- [ ] `python -m unittest discover -s tests -v`
- [ ] Schema/migration check against a disposable PostgreSQL database.
- [ ] Inspect diff and ZIP integrity.

## Telegram/production checks
- [ ] Authentication only succeeds with valid Telegram initData.
- [ ] Feed, following, profile, search, saved viewer and notifications work.
- [ ] Single/double tap and rapid like requests are correct.
- [ ] Comment create/delete and counter consistency are correct.
- [ ] Delete confirmation cancel/accept/error paths are correct.
- [ ] Share link opens correct video inside Telegram Mini App.
- [ ] Test bottom screen, safe areas, keyboard, app resume, and slow network on Android.
- [ ] Verify actual poster URLs exist and load.
- [ ] Monitor Railway logs after deployment; roll back if critical errors appear.

Do not mark a checkbox complete without performing that check. Static checks do not replace device/production checks.
