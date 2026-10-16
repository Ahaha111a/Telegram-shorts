# Changelog

## Audit remediation — 2026-10-16

- Removed the strong bottom gradient and vignette layers from the feed; removed the large upward shadow/gradient from the bottom navigation.
- Reworked video tap handling so single-tap action is deferred and double-tap like is deduplicated.
- Added explicit desired-state support to like API and wrapped like mutation/count refresh in a transaction with row locking.
- Made comment create/delete and authoritative counter refresh transactional.
- Replaced native confirm dialogs for video/comment/moderation deletion with a shared accessible confirmation dialog.
- Added Telegram share-link API usage and `start_param` deep-link handling.
- Added `poster` from `thumbnail_url`, disabled eager metadata preload in profile tiles, and aligned profile stats with CSS Grid.
- Primary content panels use full-screen layout; history UI removed, database/backend compatibility retained.
- Added `tests/test_quality_regressions.py` and `.env.example`.

Validation status: static tests are intended to run with this package. Telegram Android, production API/DB, BotFather deep link and visual viewport checks remain manual and are not claimed as passed.
