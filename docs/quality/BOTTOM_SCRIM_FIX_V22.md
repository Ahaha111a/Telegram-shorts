# Telegram Shorts v22 — main-feed bottom dark band

## Implementation
- Build marker and `/health/build` now identify v22.0.0.
- Main feed CSS was given a single final full-bleed contract for viewport sizing and overlay removal.
- The feed template already omits the obsolete `.video-gradient` node; all remaining pseudo-element/overlay candidates are forcibly removed.
- Main-feed video is overscanned and shifted upward to crop the lower portion of a source if a dark fade is baked into the media. Profile video viewer framing is unchanged.
- The profile viewer and backend API logic are retained.

## Trade-off
The main-feed video is zoomed and reframed (approximately 1.26x) so the lower edge of a media file cannot contribute a baked-in dark fade. This may crop some image detail at the top, bottom, and sides. The profile viewer retains its prior framing.

## Verification
Static checks: Python compilation, inline JavaScript syntax, ZIP integrity, build marker/health route consistency, and absence of a feed `.video-gradient` node.
Real-device rendering and Railway deployment cannot be verified from this archive alone. Confirm `/health/build` reports `v22.0.0` after deployment, then inspect the feed in Telegram.
