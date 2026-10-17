# Strict frontend error repairs — 17 October 2026

All **524 remaining Svelte/TypeScript errors** reported after `fb30d2e7c` are resolved. Strict checking and JavaScript checking remain enabled, and application files remain included. The existing **195 warnings** are still reported; this pass does not suppress them.

## Repairs

- Replaced implicit state and callback types with concrete contracts for editor drafts, authentication/MFA results, chat socket events, channels, attachments, terminal files, model settings and resource lists. Socket permission notifications can omit message IDs without indexing history with an absent value.
- Fixed a missing `await` that reported a successful vector-database reset before the request completed.
- Preserved original model tag arrays while constructing search text, and avoided sorting the shared tag array in place. Default capability values retain explicit booleans and omit unset values.
- Tool/function editor imports validate content, metadata, translations and permissions before replacing the form. Malformed saved drafts show an error. Community imports require both an allowed origin and the opener window; their listeners are removed on unmount.
- Editor language loading no longer prevents synchronous cleanup registration. Artifact frame listeners are removed on reload/unmount, and drag prevention no longer adds repeated listeners on mouse entry. DOM and file operations check unavailable elements, canvas contexts, file data and selections.
- Read-only message views receive safe optional callback defaults. Shared chat loading, channel submissions and optional attachment fields match their actual API contracts. Call-panel identifiers and optional status/profile fields are normalized where needed.
- Markdown uses a typed extension that preserves literal single tildes and standard double-tilde deletion. Empty iframe sandboxes remain explicit. URL validation returns a boolean rather than incorrectly narrowing every non-URL string to `never`.
- Frontend CI now runs the strict check before its test suite. The combined lint command stops on a failing stage, and obsolete Prettier plugin-search settings were removed.

## Verification

- `npm run check`: **0 errors, 195 warnings** (exit status 0).
- Frontend tests: **93 passed across 39 files**, including malformed plugin drafts, permissions, translations, prototype-like locale names and Markdown behavior.
- Node 22 production build with `USE_SLIM=true`: **passed**. This skips optional Pyodide package downloads.
- Chromium production smoke tests with mocked APIs: **passed** for admin policy saves, account lookup and reason gating, read-only note loading/unmount, chat input, notes search retry and stale-response handling, plus shared-chat history, Markdown rendering and read-only composition.
- npm audit: **0 advisories** in the resolved dependency tree.
- Branding audit passed; retained upstream legal notices remain intact.
- Modified-file formatting and whitespace checks: **passed**.

No backend source changes were made. Backend regression tests were not rerun for these frontend changes. Real email delivery, payment settlement, collaborative Socket.IO traffic and live provider calls were not exercised by the browser mocks. The previously documented Accelerate/ChromaDB advisory limitations remain; resolving frontend diagnostics does not certify the entire system against unknown vulnerabilities.
