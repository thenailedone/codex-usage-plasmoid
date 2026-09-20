# Changelog

## 1.2.0 — 2026-09-20

- Derive compact and expanded labels from each reported window duration.
- Support one, two, or many usage windows without fixed five-hour/weekly assumptions.
- Prefer Codex's multi-bucket `rateLimitsByLimitId` response and fall back to the legacy bucket.
- Show the first two windows in the panel with a `+N` indicator and every window in the popup.
- Treat an empty window list as a valid, informative state instead of an error.

## 1.1.0 — 2026-09-19

- Add managed ChatGPT sign-in through the local Codex app-server.
- Reuse existing Codex authentication without reading token files.
- Add public packaging, tests, release automation, and store metadata.
- Improve missing-Codex, signed-out, loading, and error states.

## 1.0.0 — 2026-09-19

- Initial Plasma 6 panel widget with five-hour and weekly remaining usage.
