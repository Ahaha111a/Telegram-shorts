# Bug prevention rules

- Never modify a single gradient without searching all overlays, pseudo-elements, fixed panels, shadows, and safe-area layers that affect the same region.
- For gestures, define one owner per gesture. Do not independently toggle the same state from `click`, `dblclick`, `pointerup`, and touch handlers. Delay single-tap actions until the double-tap window closes.
- Use explicit desired-state API requests for rapidly repeated mutations where possible. Keep legacy toggle behavior only for backwards compatibility and serialize UI requests.
- Counters must be derived from authoritative rows inside a transaction; never trust client-submitted totals.
- Destructive operations must use the shared confirmation UI, disable repeat submission, enforce ownership on the backend, and report failure without removing data from the UI.
- Escape user-controlled text before inserting it into HTML. Validate authorization on every backend operation; never rely on UI visibility as access control.
- Video thumbnails require a real `thumbnail_url`; do not claim a poster exists when the source data is empty.
- Share links must use Telegram Mini App deep links and be tested with BotFather configuration; a website URL is not equivalent.
- Root sections and action sheets have different navigation semantics. Do not apply bottom-sheet transitions to primary sections.
- Avoid broad refactors without regression tests. Compare all changed API contracts with every frontend caller.
- Before editing, compare the supplied archive with GitHub `main`. Never silently overwrite a newer source with an older ZIP.
- No release is “verified” until static checks, API/DB tests, and real-device scenarios are reported separately.
