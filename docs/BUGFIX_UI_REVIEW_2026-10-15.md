# UI and security repair continuation: 15 October 2026

This review continues from `400a8990d7be91dadf6e47342373384d07eccdbb`. It repairs confirmed frontend failures and tightens the contracts used by channels, chat, settings, resource imports and exports. It does not establish that the repository is free of unknown vulnerabilities.

## Security and runtime repairs

- CSV exports for evaluations, user directories and chat tables now neutralize spreadsheet formula prefixes as well as escaping quotes, separators and line breaks. Attacker-controlled names, comments and generated table cells cannot become formulas through these export paths.
- Tool connection imports and OAuth registration no longer print imported credentials or returned registration information. Root tool execution no longer prints server connection objects, execution payloads, results or backend configuration.
- The Markdown file preview iframe now explicitly permits static same-origin display and downloads without allowing scripts. The existing untrusted HTML preview retains its separate sandbox policy.
- Python socket executions use isolated request IDs and remove listeners on completion, failure, timeout and teardown. A failed or timed-out shared worker is terminated and cleared, allowing replacement. Worker acquisition occurs after attachment downloads and checks teardown before execution. Results retain the established stdout/stderr/result callback shape.
- Tool and function settings capture resource identifiers and serialized values before saving. Loading ignores superseded responses; delayed saves are cancelled on resource changes and teardown. Pending saves cannot replace newly edited values. Numeric enum values retain their original types, and coordinate input is validated before reaching Leaflet.
- Speech model loading shares an in-flight request, invalidates it when the engine changes, disposes late results and releases models on teardown. Browser voice updates use an event listener with cleanup.
- Citation grouping validates documents, normalizes numeric identifiers and preserves metadata and score positions when earlier entries have missing metadata. Feedback display tolerates missing or malformed snapshots.
- Character-card imports tolerate non-text metadata and reject truncated or overflowing PNG chunk lengths. PDF export removes its temporary DOM even when rendering fails.
- Knowledge-base loading follows route changes and ignores late responses. Keyboard, drag, typing, worker and selection resources have explicit cleanup in the affected components.
- File, prompt, tool and model imports await file reads and report failures. Channel uploads await completion, and channel message rendering tolerates boolean data payloads returned by the slim backend.
- Ollama version lookup now preserves connection index zero. The shared textarea forwards keyboard shortcuts, and accessibility labels reach sensitive inputs.

## Type checking

The strict Svelte/TypeScript check remains enabled, with all application files included. Standard DOM async-iteration declarations were added for file-system access. Diagnostics are repaired through concrete resource, event and callback contracts and runtime guards; no application exclusions or type-check suppression were added.

Final count: **524 errors and 195 warnings across 206 files** (1,397 fewer errors). The starting count for this continuation was **1,921 errors and 194 warnings**. A successful production build does not resolve outstanding strict diagnostics.

## Validation

- Frontend regression suite: **83 passed across 37 files**. New regressions cover CSV escaping, citation alignment, malformed character imports, prompt normalization, settings serialization, numeric enums, keyboard shortcuts, stale settings responses, PDF cleanup and late speech-model delivery.
- Production build: **passed**, on Node 22 with `USE_SLIM=true` (optional Pyodide package downloads skipped).
- Chromium smoke tests passed with mocked APIs: administrator policy save, account lookup and reason gating; read-only note load/unmount; chat input; notes list, failed-search retry and stale-response isolation. Socket.IO is not implemented by the mock.
- npm audit: **0 advisories** in the resolved dependency tree.
- Branding and whitespace validation: **passed**.
- No backend source changes were made in this continuation. The previous backend regression result was **139 passed**; it was not rerun for frontend-only changes.

## Outstanding limits

The unresolved Python dependency advisory records for Accelerate 1.13.0 and ChromaDB 1.5.9 remain as documented in [the previous continuation](BUGFIX_CONTINUATION_2026-10-15.md). This frontend work does not remediate an independently deployed Chroma server. Email delivery, payment settlement and real OpenAI/Gemini calls were not exercised against external services.
