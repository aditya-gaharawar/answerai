# Continued bug fixes: 15 October 2026

Later fixes and current validation are documented in [the UI repair continuation](BUGFIX_UI_REVIEW_2026-10-15.md).

This pass continues from `7c8fcfd76` and the earlier [bug-fix review](BUGFIX_REVIEW_2026-10-15.md). It repairs confirmed failures and expands regression coverage. It does not establish that the repository is free of unknown vulnerabilities.

## Changes

- Model snapshot validation now checks Accelerate's flat parameter-to-shard indexes as well as indexes containing `weight_map`. Traversal, absolute filenames, null maps and malformed maps are rejected; valid flat indexes remain supported.
- Camera, microphone, screen capture and voice-recording cleanup release late-granted streams after unmount. Recording failures release tracks and audio analysis resources. Speech-worker initialization is shared, pending requests reject on failure/termination, and old workers cannot fail a replacement worker.
- Model downloads check request ownership before accepting progress or removing a row. Cancellation removes the captured row before aborting, handles a rejected stream cancellation, and preserves replacement downloads.
- Code-block execution uses unique request IDs. Completion, timeout and unmount remove request listeners without replacing another consumer's error handler. Timed-out replies cannot populate a newer execution. Output normalization separates inline PNGs from text and preserves structured results.
- Root layout and sidebar initialization register cleanup synchronously. Fetch wrapping, subscriptions, keyboard handlers, drag resources and timers have corresponding cleanup. Admin/functions and workspace/models no longer return ignored asynchronous mount cleanups.
- Notes search ignores stale responses, preserves the successful pagination cursor after failures and offers retry. Search previews also ignore stale requests. Folder trees handle missing parents, cycles, shared entries and prototype-like IDs.
- Chat attachments await file reads, conversion and upload instead of detaching asynchronous callbacks. New image attachments are discarded when their target chat changes during conversion. Extracted document text is no longer logged by the composer.
- Direct completion streams retain incomplete lines across network chunks. Stop-token decoding handles malformed escapes. Chat imports retain a consistent graph when source nodes are unsupported or missing. OpenAPI reference resolution stops circular references and retains schema constraints.
- Shared model, message, folder, editor and plugin contracts replace many implicit types. Prompt-selection and editor event contracts now match the values emitted by their components. Chat direction is normalized for DOM attributes. The toast dependency now supports Svelte 5.
- Function imports await file reading and report malformed input; active toggles await server updates before refreshing models and restore the displayed state when an update fails.

## Validation

- Backend regression suite: **139 passed**, including the expanded 19-case model snapshot suite.
- Frontend regression suite: **66 passed across 27 files**. New cases cover delayed media permissions, worker shutdown/retry, request isolation, cancelled downloads, stream chunk boundaries, recursive schemas, import graphs and output normalization.
- Production build passed on Node 22 with `USE_SLIM=true`; optional Pyodide package downloads are skipped.
- Chromium production smoke passed with mocked APIs: administrator policy save/account lookup/reason gating, read-only note loading/unmount, chat input, notes list defaults, search failure/retry and stale-response isolation. The mock does not implement Socket.IO; collaborative synchronization and real provider calls were not exercised.
- npm audit: **0 advisories** in the resolved dependency tree.
- Branding audit passed. Modified Python snapshot code/tests pass Ruff; whitespace checks passed.

## Remaining work

The strict Svelte/TypeScript check still fails: **1,921 errors and 194 warnings across 248 files**, down from 3,095 errors at the start of this pass (1,174 fewer errors). Strict checking remains enabled and application files remain included. Major remaining concentrations include channel components, the main chat component, root layout and connection settings. A successful production build does not resolve these diagnostics.

The resolved Python dependency audit reports **six advisory records across Accelerate 1.13.0 and ChromaDB 1.5.9**, including a duplicate Chroma record. The audit data provides no fixed versions for these records. Accelerate 1.15.0 was also inspected; its checkpoint index path join still requires application-side validation. This pass strengthens that validation rather than removing the advisory by changing a version string. Chroma's independently deployed server authentication/RBAC and embedding-code issues still require remediation in that server; application tests do not certify the server.

Email delivery, Stripe/Razorpay settlement, OpenAI/Gemini calls and optional large ML runtimes have not been exercised against paid services. Automated provider checks use mocks.
