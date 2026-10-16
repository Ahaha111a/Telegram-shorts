# Bug prevention

## Known/recurrent classes
- **Bottom darkening:** feed `.shade` had a bottom gradient ending in `#000d`; `.vignette` added inset black shadow; bottom nav had its own gradient and upward shadow. Audit all three layers together. Device screenshot is required to confirm final appearance.
- **Duplicate gesture events:** touch `pointerup` and synthetic `dblclick` can both toggle a server-side like. Ensure one gesture causes one request; test real Android WebView.
- **Scroll snap geometry:** cards using `100dvh` inside a shorter panel cause scroll offset mismatch and multi-item/partial swipes. Card height must match actual scroll viewport.
- **Missing previews:** database has `thumbnail_url`, but frontend previously did not select/use it. Every SQL projection and render surface must carry it. Older rows can still lack thumbnail.
- **False “fixed” reports:** code changes are not visual proof. Record the test method and its limitations.
- **Archive/repository drift:** compare Git blob SHA for all authoritative files before editing. Do not use older generated ZIP as source when a newer user ZIP is provided.

## Mandatory prevention
- Search all definitions and duplicate CSS overrides before changing styles.
- Trace an action from gesture → handler → API → DB mutation → response → every visible button/count.
- Avoid blind toggle API retries: a retry can reverse the intended state.
- Run regression checks on every related viewer, not just the feed.
- Keep exact test evidence and unresolved risks in `CHANGELOG.md`/audit report.
