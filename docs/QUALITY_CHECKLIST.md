# Release Quality Checklist

## Authentication and authorization
- [ ] Open only through Telegram Mini App; missing or invalid `initData` is rejected.
- [ ] Verify signature, required `auth_date`, freshness and future timestamp.
- [ ] Confirm all mutations derive the actor from verified `initData`, not a client-supplied ID.
- [ ] Verify owner-only video/comment operations and admin-only moderation.

## Feed and video playback
- [ ] One vertical gesture advances one item; end-of-feed loads more or shows a real empty state.
- [ ] At most one feed video plays; previous video pauses.
- [ ] Test autoplay rejection, muted fallback, missing URL, buffering and retry.
- [ ] Single tap toggles playback; double tap likes without pausing; taps on controls do not bubble.
- [ ] Meaningful view threshold and server-side deduplication are consistent.

## Social state and counters
- [ ] Like/save/follow operations are unique per user and target.
- [ ] Retry with explicit desired state does not invert the action again.
- [ ] Counters are recomputed from canonical rows after mutations.
- [ ] Comments, replies and comment likes are persisted; editing and pinning are permission-checked.
- [ ] Comment deletion requires confirmation; child replies cascade and count is recomputed.
- [ ] Follow counts agree between profile, lists and search.

## Profiles and privacy
- [ ] Own and other profiles load correctly; private saved/history data is only returned to the owner.
- [ ] Follow/unfollow and profile editing persist after reload.
- [ ] Long names, bios and usernames do not overflow small screens.

## Upload and deletion
- [ ] Reject unsupported MIME types and files over 50 MiB.
- [ ] Storage upload failure creates no database video row.
- [ ] Database insert failure attempts to remove the uploaded object.
- [ ] Deletion is owner-only and confirmed by the UI; check storage cleanup in Supabase.
- [ ] Validate upload progress and timeout behavior on a real mobile connection.

## Navigation and mobile
- [ ] Profile, comments, search, notifications and other primary sections occupy the full viewport.
- [ ] Back button / Telegram BackButton returns through navigation history.
- [ ] Return restores the previous feed item and approximate playback position.
- [ ] Check safe areas, `100dvh`, keyboard, narrow widths, orientation and Telegram WebView.
- [ ] Check reduced-motion settings and avoid horizontal overflow.

## Network and resilience
- [ ] Test loading, empty, error, retry, slow network and repeated rapid taps.
- [ ] No failed mutation leaves an optimistic false state.
- [ ] API errors do not expose secrets or stack traces.

## Release and deployment
- [ ] `python scripts/quality_check.py` passes.
- [ ] Apply additive migrations before deploying changed API code.
- [ ] Confirm Railway startup logs, `/health`, `/health/db`, and Mini App smoke test.
- [ ] Test final ZIP opens and contains expected files.
