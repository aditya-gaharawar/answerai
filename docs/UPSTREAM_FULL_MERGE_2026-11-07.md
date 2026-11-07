# Complete upstream main integration — 7 November 2026

ANSWERAI now integrates upstream main through `c38885a1a737da4968f157092f304f3b5481d0bf` (0.13.0), including all 679 commits after the previously integrated `91ea4e3421d1d8069f13d4a463fcb5986d94ea60`. This is a real merge with upstream ancestry. It supersedes the eight-backport-only scope in [the earlier report](UPSTREAM_BACKPORTS_2026-11-07.md).

## Result

The integration includes upstream sub-agents and agent tools, MCP applications, the tabbed workspace, browser and desktop support, Git/file panels, side chats, notifications, comments, multi-page notes, configuration additions, translations, documentation, and dependency changes. Backend paths and imports remain `backend/answerai` and `answerai`. ANSWERAI branding, assets and domains are retained with required upstream legal attribution.

Existing ANSWERAI email verification, MFA/session revocation, administrator controls, billing, Stripe/Razorpay integration, plan limits, connector catalog and setup, and OpenAI Realtime/Gemini Live call handling remain integrated. The model-list and execution paths retain plan checks; generation still reserves quota. The new tabs use the ANSWERAI call panel and its existing provider/media lifecycle. The discarded UI redesign was not restored.

The database has a single merge revision, `c7d1e32b8a09`, joining the ANSWERAI billing/authentication chain and upstream's new migration chain. Fresh installation and upgrades from existing ANSWERAI data preserve billing records. Multi-page notes normalize existing single-page content.

## Compatibility repairs

- Kept the existing SvelteKit 3 / TypeScript 6 toolchain and upgraded upstream adapter/plugin additions to compatible versions. Normal installs use `npm ci`, without force.
- Matched the Python dependency additions while preserving newer security requirements; regenerated `uv.lock`. Docker and package-release builds use Python 3.12 and Node 22.
- Included local dependency sources in source distributions so isolated package builds can resolve them.
- Retained safe tool-argument parsing, permission checks for uploaded files, asynchronous audio cleanup, PDF-export cleanup, stale-search protection and session-bound terminal availability checks.
- Resolved frontend types, null handling, accessible markup and obsolete prop plumbing with strict checks enabled. Compiler exemptions are confined to documented remote input surfaces, keyboard-operable separators and delegated event containers.
- Updated vulnerable transitive Glob/Minimatch versions. Deepmerge 4.3.1 has no published patched release at integration time; its MIT CommonJS distribution is vendored with own-property writes to prevent prototype poisoning in both merge-copy paths. Regression tests exercise hostile JSON on both sides and normal merge behavior.
- Preserved the verified upstream encryption distribution and source manifest, including protocol identity constants. Browser runtime preparation includes noVNC attribution.

## Validation

- 203 backend tests passed, including billing/live/email/security, agent-tool permissions, and fresh/existing database migrations.
- 101 frontend tests passed across 43 files, including three dependency-security regressions.
- Strict Svelte/TypeScript checks: zero errors and zero warnings.
- Source distribution builds with a clean frozen dependency install and includes both local frontend dependencies.
- Production frontend build passed. Encryption source/checksum verification and actual WASM round-trip, replay rejection and session-binding checks passed.
- Runtime API smoke passed for health, configuration, billing, live providers, email settings, admin controls, connectors, sub-agent settings, notifications and search. Note creation, legacy normalization and second-page persistence passed against a fresh SQLite database.
- Browser fixtures passed for the original composer, search/stale-response/failure recovery, and Gmail, Slack, GitHub and Notion connector setup. Authenticated browser checks also exercised the real slim backend and persisted notes.
- `npm audit` reports zero vulnerabilities. Python formatting, fatal correctness checks and branding audit passed.
- Gitleaks scanned the tracked source snapshot. Its only match is the public Rust dependency name `libcrux-secrets` in Cargo.lock; it is not a credential.

## Screenshots

[Chat](screenshots/upstream-20261107/chat.png) · [Workspace search](screenshots/upstream-20261107/workspace-search.png) · [Gmail](screenshots/upstream-20261107/gmail-setup.png) · [Slack](screenshots/upstream-20261107/slack-scope-check.png) · [Notion](screenshots/upstream-20261107/notion-oauth.png) · [Real backend note](screenshots/upstream-20261107/runtime-multipage-note.png)

## Validation limits

SMTP delivery, paid transactions, external OAuth authorization, model inference and realtime provider connections were not exercised with production credentials. Runtime verification used the slim backend and local test data. Optional ML integrations, external terminal/browser servers, and distributed Redis/load/failure behavior were not exhaustively exercised. The merge does not constitute a production deployment or a guarantee that no vulnerabilities remain.
