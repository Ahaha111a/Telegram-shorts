# v20.0.0 — full-bleed feed and profile viewer scrolling

## Root-cause findings from v19 source

1. The previous CSS had many repeated regression-guard blocks, but the app still depended on a measured viewport value captured before `Telegram.WebApp.expand()` and preferred `Telegram.WebApp.viewportHeight` even when it could be stale. The bottom area could therefore be exposed by a viewport-height mismatch. v20 reads `visualViewport.height` first, then `innerHeight`, and refreshes after resize, page show, orientation changes, and Telegram `viewportChanged`.
2. The profile/saved video viewer was styled as a generic bottom-sheet `.panel` (`max-height`, automatic height, outer `overflow:auto`) while its inner `.viewer-track` and each `.viewer-item` were sized to 100% / `100dvh`. The parent did not have a definite full-screen height, so the inner track did not have a reliable scroll container. v20 makes the viewer panel fixed and full-screen, gives the shell and track definite heights, and sizes each item to the same measured viewport.
3. The initial server used `Path("dist")`, which depends on the process working directory. v20 resolves the static directory relative to `bot.py`, avoiding accidental selection of a different or missing `dist` directory if Railway starts the process from a different working directory.

## Changes

- Removed the transparent top-safe overlay node from each feed slide; retained controls and metadata above the video.
- Added explicit full-bleed sizing and disabled pseudo-element/scrim layers on the feed video stack.
- Added full-screen scrollable profile/saved viewer with native vertical scrolling and snap points.
- Initial viewer scroll now uses the actual rendered viewer-item height instead of `window.innerHeight`.
- Added `GET /health/build`, returning build `v20.0.0`, index existence and byte count; home response includes `X-Telegram-Shorts-Build: v20.0.0` and no-cache headers.
- Resolved `DIST_DIR` relative to the deployed `bot.py`.

## Validation performed locally

- `node --check` passed for the inline JavaScript extracted from `dist/index.html`.
- `python -m py_compile bot.py` passed.
- Confirmed build marker, new viewer CSS, height-based viewer scroll and removal of the feed overlay node.
- ZIP integrity checked after packaging.

## Remaining real-device check

Static checks cannot prove how Telegram's Android WebView renders a live uploaded video. After deployment, check `https://telegram-shorts-production.up.railway.app/health/build`; it must report `v20.0.0`. If it does not, the active Railway service/branch is not serving this build. Then reopen the Mini App and test the bottom edge and swipe scrolling through at least three profile videos. Do not label the issue fixed until that device check succeeds.
