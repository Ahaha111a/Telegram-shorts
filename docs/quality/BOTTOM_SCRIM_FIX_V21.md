# v21 — main feed viewport and bottom scrim audit

## Changes
- Replaced viewport sizing routine: WebView layout viewport is primary; Telegram viewport values are used only when consistent.
- Applies measured height to app/feed and existing slides; slides inherit the same CSS variable when appended.
- Main feed is fixed to the viewport; slide layout/paint containment is removed to avoid clipping differences in Android WebView.
- Disables feed-specific scrim/pseudo-element layers and removes the splash element after fade-out.
- Build marker updated to v21.0.0.

## Limits
Static checks cannot prove what Railway serves or what Telegram Android WebView paints. Confirm `/health/build` reports v21.0.0, then inspect the main feed on-device. If the band remains while the same source video is clean in the profile viewer, the live WebView's feed/video rectangles must be measured; that would indicate runtime sizing or media rendering rather than a remaining gradient.
