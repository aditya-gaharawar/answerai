# Upstream integration — 24 October 2026

Integration branch: `integrate/upstream-main-20261024`.

The branch integrates upstream main commit `91ea4e3421d1d8069f13d4a463fcb5986d94ea60` (version 0.12.3), with 112 upstream commits since the previously integrated `bd495677ab7835a37a2914ada66f4541e5e7ce46` (0.12.1). The starting ANSWERAI branch was `feat/external-connectors`, commit `2d832c205db5a74e8d92a45da07bef4981241562`. Upstream ancestry is retained in a Git merge; the application tree was not replaced.

## Included upstream changes

- Permission-scoped workspace search across accessible chats, channel messages, and notes, including result previews, filters, deep links, and retry/stale-response handling.
- Redis streaming storage and room-delivery improvements.
- OAuth token refresh fixes, tool selection after authorization redirects, and deferred tool discovery/dispatch improvements.
- Optional encrypted private channels, disabled by default and controlled by administrator/user permissions.
- Compare-view options and undo; richer document/Markdown previews, comments, and terminal-file questions.
- Per-page PDF export for long documents and chats, read-aloud continuation fixes, shared-chat collaboration/access improvements, and translation updates.
- The Drive picker now requests access to picked files only. The separate Drive connector's explicitly configured metadata scope remains unchanged.

## ANSWERAI functionality preserved

Billing, Stripe/Razorpay payment handling, rate/feature quotas, signup email verification, administrator controls, OpenAI/Gemini live calls, the realtime client, and the connector catalog/service remain byte-identical to the starting branch. Authentication and permission changes retain our verification and plan enforcement. Native argument parsing, CSV formula protection, media cleanup, and strict frontend types are preserved.

The previous UI redesign remains reverted. Upstream functional UI additions are included without restoring the discarded landing-page redesign or its Agent/thinking toolbar.

Branding and package paths remain ANSWERAI/AAI under `backend/answerai`; legal attribution is retained. Translation additions were merged by key. The verified upstream encryption source/distribution remains unmodified. Its cryptographic identity domain separator is deliberately retained as a protocol constant, with a narrowly scoped branding-audit exception; changing that constant would change identity keys and invalidate the supplied artifact verification.

The existing asset preparation already copies ONNX assets. Encryption license attribution is copied into generated static assets by that same preparation step, avoiding an incompatible additional Vite plugin. Builds verify the committed encryption source fingerprint and distribution checksums; no Rust toolchain or crypto download is required for normal builds.

PDF comment rectangles use the PDF.js 6 point-conversion API, preserving our existing PDF.js security upgrade. The long-note PDF export retains `finally` cleanup of its temporary DOM, including rendering failures. Frontend typing and nullability regressions from conflict resolution were repaired with strict mode kept enabled.

## Validation

- **196 backend tests passed**, including existing billing/live/email/security/migration regressions and three new workspace-search data-isolation tests. The latter cover private records, explicit note grants and revocation, and shared snapshots versus private live chats.
- **98 frontend tests passed across 42 files**, including new PDF rectangle projection checks and the note-render cleanup regression adapted to per-page export.
- **Strict frontend check: zero errors and zero warnings.** `npm run check` now fails on warnings.
- **Node 22 production build passed.**
- **Real fresh-database runtime smoke passed:** health, administrator signup, billing, live-provider configuration, email settings, admin overview, connector catalog, and the new workspace-search route.
- **Actual verified WASM smoke passed:** two-client encrypted message round trip, replay rejection, cross-session binding rejection, and host-only member removal. Run `node scripts/encryption/smoke.mjs` with Node 22.
- **Browser checks passed with mocked APIs:** connector setup and credential failure states; account policy/reason gating; read-only notes; notes search failure/retry and stale-response protection; shared-chat history/Markdown/read-only behavior; original chat composer; and workspace-search failure/retry and stale-response protection.
- Branding audit, Python compilation, fatal Python correctness checks, and whitespace checks passed.
- Dependency upgrades resolve all reported npm advisories: **zero known vulnerabilities at every severity**. SvelteKit 3.1, adapter-static 4, Svelte 5.57+, and TypeScript 6 use the Vite-based configuration. Legacy page consumers subscribe through a tested rune-to-store adapter, preserving navigation updates. The runed 0.35 dependency chain is upgraded to 0.38 through a targeted override. The old cookie security override now applies only to pre-0.7 versions, allowing the framework to use its required cookie 2 API. Node 22.17+ is required.

## Screenshots

The screenshots use controlled fixtures, not live user/provider accounts.

[Original chat interface](screenshots/upstream-20261024/chat.png) · [Workspace search](screenshots/upstream-20261024/workspace-search.png) · [Gmail connector](screenshots/upstream-20261024/gmail-setup.png) · [Slack credential checks](screenshots/upstream-20261024/slack-scope-check.png) · [Notion OAuth setup](screenshots/upstream-20261024/notion-oauth.png)

## Limits

No deployment was performed and production user data was not accessed. SMTP delivery, real model/live-provider calls, paid gateway transactions, and account authorization to external connectors require deployment credentials and were not tested live. Runtime smoke used the slim backend. Full optional ML dependencies and multi-instance Redis/load/failure behavior were not exercised. The WASM test does not replace a complete deployed encrypted-channel/security review.

The integration and follow-up repairs are merged into `main` in both the application repository and the private internal repository. The internal repository retains its historical workspace archive and keeps archived workflows inactive.

## Final repairs before merging

- Repaired ambiguous HTML tags, removed dead scoped CSS and obsolete component prop plumbing, and connected previously ignored close, sharing, and empty-state props.
- Replaced pointer-only dirty-state observation with reactive binding observation; fixed nested file-card buttons, missing accessible names, and combobox/listbox relationships. The original interface remains in place.
- Existing keyboard-operated document viewers and event-delegation containers have narrowly documented compiler exemptions; user-uploaded videos still have no caption attachments. No global diagnostic suppression was added.
- Frontend CI uses the frozen lockfile without force, audits dependencies, verifies branding/encryption integrity, builds, and runs strict diagnostics and tests. Formatting and translation generation are no longer run as source-mutating CI checks. Python formatting and fatal correctness checks pass.
- The branding audit excludes the historical `internal-workspace/` evidence archive, preserving its original hashes and contents.
- A fresh browser pass covers the original composer, workspace-search stale/failure recovery, Gmail/Slack/GitHub/Notion connector setup, administrator policy gating, read-only notes, and shared chats. Provider APIs are fixtures; live payment, SMTP, and AI-provider credentials were not exercised.

[Administrator security controls](screenshots/main-fixes-20261024/admin-security.png)
