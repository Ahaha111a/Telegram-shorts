# Bottom screen scrim — v17

## Change
Added a last-in-cascade CSS kill switch in `dist/index.html` to disable background images, masks, pseudo-element overlays, filters, opacity fades, and shadows on the app/feed/video layers. The video pixels are explicitly forced to full opacity with no mask/filter. This covers app-level overlays that remain fixed while feed slides scroll, not only `.video-gradient`.

## Replace in GitHub
- `dist/index.html`

## Verification limits
Static checks can confirm the rules exist and parse, but cannot prove the Telegram Android WebView is not applying an external overlay or serving cached HTML. After deployment, hard-reload/reopen the Mini App. If the same gradient remains with these rules active, inspect the live DOM/computed styles and deployed HTML response before changing video CSS again.
