# Product specification — Telegram Shorts

## Core experience

Telegram Mini App for short vertical videos. Primary loop: open feed → watch one active video → like/save/comment/share → open creator profile → continue watching or return to feed.

## Supported core features in source

- Recommended and following feeds with vertical scroll snapping.
- Autoplay of the active feed item via `IntersectionObserver`; other feed videos are paused.
- Like/save/report/hide actions and server API integration.
- User profile, following relationships, profile video grid, saved videos, search and notifications.
- Video upload and owner-only soft deletion.
- Comments with create/list/delete-own-comment behavior.
- Telegram `initData` authentication and Telegram Mini App share deep links.

## Product rules

- Do not show a watch-history section in the UI. Retain existing database/API structures until a separately approved migration.
- Do not add an in-app camera without explicit approval.
- Every delete operation requires explicit confirmation; cancellation must be side-effect-free.
- Counts must reflect authoritative server data. Frontend must never write totals directly.
- A double tap on the video surface toggles the like state exactly once and must not pause/resume playback.
- Action icons are outline/filled SVGs with no decorative square tile behind them; preserve a usable touch target.
- Profile counters use equal grid columns and tabular numerals.
- Main sections (profile/search/saved/notifications/people/admin) use full available viewport; action sheets can remain modal.
- Share links must open the Mini App via Telegram `startapp`, not a generic web URL.
- `thumbnail_url` is optional; if absent, UI must not pretend a poster was generated.

## Known gaps requiring a separate implementation

- Comment replies are not supported by the current `comments` schema (no `parent_id`) or API.
- Automatic thumbnail generation/storage is not present in the audited upload path.
- Recommendations are a basic server ranking, not a trained personalization system.
- Real device and production integration status must be recorded separately from static checks.
