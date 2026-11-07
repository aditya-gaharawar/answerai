# Agent and search reliability

The quota changes from PR #5 are merged into main. This follow-up improves the existing agent execution and search paths without replacing the chat interface.

- Synchronous Python plugins execute in a worker thread, preserving request context variables. An async result returned by a sync wrapper is awaited.
- Missing required tool arguments produce a repairable error before execution. Existing permission checks and approval staging remain in place; MCP servers continue validating their own schemas.
- Tool execution has a default 180-second wall-clock budget, or 600 seconds for built-in image generation/editing. Set AGENT_TOOL_TIMEOUT_SECONDS to a finite value from 1 to 1800 seconds to override. Built-in user questions, timers and delegation retain their existing long-wait behavior. Cancellation propagates. A timeout can leave remote operations or synchronous worker threads running; the model is told to inspect state rather than blindly repeat side effects.
- Web search validates non-empty queries, respects disabled result counts, caps the result count at 50, and deduplicates URLs while preserving provider order and meaningful query parameters. Search and page fetch have 45-second deadlines. Empty pages return an explicit error. The default fetched-page text budget is 24,000 characters when no administrator value is configured; explicit administrator values retain their behavior.
- Attached-file semantic search falls back to bounded lexical retrieval when embeddings are absent, retrieval fails/times out, or no chunks are returned. Authorization is rechecked before fallback; explicit permission failures remain failures. Lexical results include source, file ID, passage offset, score and retrieval method. Work is bounded to 100 authorized files, 2 million characters per file and 20,000 candidate passages, with a small bounded heap and at most 20 returned passages. Lexical retrieval is a keyword fallback, not a claim of semantic equivalence.
- Deferred-tool discovery weights tool names, searches argument descriptions, supports case-insensitive exact names and conservative typo correction, and retains deterministic tie-breaking. Untrusted tool descriptions are escaped in the discovery manifest.
- Agent guidance encourages reading source pages/passages, correcting tool arguments, checking state after timeouts and verifying task completion.

Regression coverage exercises cancellation, timeouts, required arguments, event-loop responsiveness, context preservation, URL deduplication, disabled search, empty fetches, lexical ranking, permission revocation and discovery ranking/escaping. Backend CI runs the complete test suite, including the existing quota/security/agent regressions.

The execution workspace became unavailable during implementation. Verification for this branch runs through GitHub Actions; no live model, connector or external search credentials are exercised by the regression tests.
