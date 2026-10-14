# ANSWERAI system repair and validation — 14 October 2026

This review starts from merged commit `362350c`. It fixes the two reproduced findings from the previous scan and additional integration defects found while tracing signup verification, billing, admin controls and live-call lifecycle code. It is not a claim that every line or every optional integration is error-free.

## Changes

- **AAI-2026-105 fixed:** the generic OpenAI provider proxy requires an administrator, regardless of HTTP method or billing toggle. Typed generation paths use an exact allowlist. Regular chat generation still uses its existing user/model policy; project-wide provider resources are no longer available to ordinary users.
- **AAI-2026-106 fixed:** both speech endpoints and the transcription endpoint share an atomic audio budget and the existing request-per-minute counter. Blocked accounts cannot use these routes even if billing enforcement is disabled. Administrators can set `audio_requests_per_day` in the billing screen; new Free/Plus defaults are 20/200. Existing stored plan objects without the field receive the conservative Plan default of 20 until an administrator changes it. No database migration is needed.
- TTS accepts a JSON object containing nonempty text, with a 4,096-character input cap and a 64 KiB body cap. This validation precedes cache/provider work on both speech controllers. Existing TTS/STT permissions still apply; the new budget counts requests, including cached responses.
- Malformed generation JSON returns 400, rather than an unhandled parsing error. Invalid/non-ASCII or oversized webhook signatures return 400. Payment API responses must be JSON objects; malformed catalogue entries do not break the plans screen.
- Verification/public billing URLs reject malformed ports, whitespace and control characters. Administrator account lookup normalizes email casing and surrounding whitespace.
- Live calls use a bounded provider connection handshake. Browser cancellation during audio startup no longer initiates a late microphone request; late microphone grants are stopped. Stale socket errors cannot end a newly connected call. Socket handlers, timers and audio contexts are cleaned up on disconnect.
- Camera acquisition is guarded against concurrent clicks and stale permission results. Call timers stop on transport failure. Transcript saving now has the correct promise type.
- CI includes the new security and integration regression files. The old scan's expected-failure markers are removed: fixed security expectations must now pass.

## Validation and scope

The backend suites exercise email issue/resend/consume/expiry, SMTP failure handling, auth/session revocation, admin permissions, payment signatures and refund reconciliation, atomic quota reservations, model restrictions, fresh database migrations, and live leases. New cases exercise proxy opt-in, restricted/blocked audio accounts, shared counters, invalid inputs, normalized admin lookup and invalid public URLs. Both Gemini and OpenAI live socket lifecycles use mocked providers with real application controllers, including setup, audio forwarding, transcription and lease cleanup.

Frontend tests exercise PCM conversion and microphone/socket cancellation in addition to the existing preview-sandbox and version-diff tests. Providers, browser media and payment services are mocked; no real payment, SMTP delivery, microphone/camera recording or provider charge is performed by these tests.

The repository-wide frontend type check was also run against an untouched checkout of `362350c`: it reports **6,035 errors and 196 warnings in 318 files**. This is an inherited backlog, not a successful type check. The call transcript type error is fixed here; the remaining repository-wide type failures require a separate broad typing/refactoring effort. Type checking has not been disabled to make the check appear green.

Known dependency advisories and deployment risks documented in the [security review](SECURITY_REVIEW_2026-10-13.md) remain. This repair does not major-upgrade the ML stack, migrate plaintext API keys, sandbox trusted Python plugins, configure merchant publishers, or certify a production deployment. External provider credentials and end-to-end merchant/SMTP/live-model tests remain required before production rollout.

## Execution results

- All **115 backend tests pass**, with no expected-failure markers.
- The **production build passes** and writes the static site to `build/`; existing Svelte/accessibility and bundle-size warnings remain.

- All 12 frontend tests pass, including three new media cancellation/reconnect cases.
- Fresh application startup succeeds with the slim/external-provider requirements in an isolated Python environment and disposable SQLite data directory. Startup migrations complete. Health, first-admin signup, billing settings/account, live settings/provider listing, email settings, and protected admin policy/overview/account inspection return successful responses.
- Launcher syntax and help output, Python Ruff formatting and selected correctness rules, changed-file Prettier formatting, Git whitespace checks, and the repository branding audit pass.
- Final frontend type check: **6,034 errors and 196 warnings in 317 files**. The complete local diagnostic inventory is `/workspace/answerai-remaining-type-errors.json`.

The startup smoke uses the slim application profile, not all optional OCR/ML integrations or a production container. The launcher was checked for shell syntax and help behavior; its full dependency-install path was not rerun. Real external services remain unverified.
