# Upstream integration: 14 October 2026

ANSWERAI integrates upstream main commit `bd495677ab7835a37a2914ada66f4541e5e7ce46` (v0.12.1), fetched on 14 October 2026. The previous upstream base was `f8ae8a6c328946dc62cd0712961a0632574581bf`. This is a Git merge with upstream ancestry retained, rather than a replacement of the ANSWERAI tree.

## Features and fixes

The update includes administrator-managed external apps in channels (disabled by default), revision comparison and merge editors, channel notification settings and mention handling, skill archive export/import improvements, voice-avatar rotation/panning/zooming, Azure OpenAI realtime configuration, and chat, model, calendar, Redis, OAuth, citation and translation fixes. Existing ANSWERAI billing, Stripe/Razorpay integration, email verification, administrator controls, quotas and Gemini/OpenAI Live Calls remain present. New upstream realtime settings extend the existing upstream audio router; ANSWERAI's separate live router is retained.

Source and translation conflicts were resolved after applying the ANSWERAI package and branding mappings to upstream changes. Legal attribution remains intact. Custom translation keys and upstream translation updates were merged by key. New backend modules live under `backend/answerai`.

Upstream added migrations for app tables and missing authentication records. ANSWERAI already had its own verification, billing and security migration branch. Merge revision `b2a10c9d8e74` joins both without changing existing revision identifiers. Tests cover a fresh database and an upgrade from the previous ANSWERAI head while preserving a paid-plan override.

The integration also preserves the local security repairs, dependency updates and frontend type improvements saved in commit `cb354f5b4`. Asset preparation skips nested npm dependency directories when copying Pyodide runtime files; Tailwind uses its explicit CSS export with the updated Vite resolver. The custom ONNX resolution condition now retains Vite's default browser conditions, preventing Svelte's server context implementation from being bundled into the browser. PDF.js was upgraded to 6.4.299 to avoid the high-severity advisory in the newly resolved 5.x release. PDF viewers use the new loading-task cleanup API and discard documents that finish loading after their view changes.

## Validation and limits

- 116 backend tests passed, including authentication, billing, payment validation, access controls, both mocked live providers, security regressions and fresh/existing database migrations.
- 12 frontend tests passed, including live-call lifecycle and audio conversion.
- Runtime smoke checks passed for health, fresh administrator signup/signin, billing, live configuration, email settings, admin controls and the registered Apps endpoint. Apps remain disabled by default.
- Branding audit, Python compilation, Ruff formatting and fatal Python correctness checks passed.
- Production builds passed with Node.js 22; the one-command launcher now checks the dependency stack's minimum Node.js 22.17 requirement.
- Chromium verified PDF.js 6.4.299 text extraction, canvas rendering, text-layer rendering and document cleanup using a generated one-page PDF.
- Chromium passed the administrator panel, policy-save, account-lookup and action-reason checks against mocked APIs using the production frontend.
- The JavaScript dependency audit reports 12 moderate entries and no high or critical entries. The locked Python audit reports six advisory records in Accelerate and ChromaDB, including a duplicated ChromaDB advisory ID; no fixed releases are listed for those findings. Audit results are not a guarantee that the application has no vulnerabilities.
- Frontend type-checking remains failing: 4,207 errors and 194 warnings in 278 files, compared with 4,250 errors before upstream integration and 6,034 before the shared type repairs. This merge does not claim to finish the inherited type backlog.

Provider credentials were unavailable, so SMTP delivery, live provider calls and paid gateway transactions were not exercised against external services. The runtime smoke used the slim backend; optional full ML dependency behavior is not covered. Dependency advisories and the remaining type backlog still require follow-up.
