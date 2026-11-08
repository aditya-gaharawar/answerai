# ANSWERAI Agentic Engine V2

## Architecture and compatibility

The application remains a Svelte 5/SvelteKit frontend and Python FastAPI backend. Authentication, plans, model permissions, provider adapters, conversation storage, tool discovery and approvals are reused.

Interactive requests enter `main.chat_completion`, prepare context and tools through `utils.middleware`, invoke the configured provider, stream structured conversation output, execute bounded tool batches and continue the model/tool loop. OpenAI-compatible and Ollama integrations retain their existing transport and persistence. V2 adds contract validation and read-tool approval rules when `params.agent_mode` is `agent`; ordinary chat keeps its approval behavior.

`/api/v1/agent-runs` persists autonomous research jobs. Each process starts a dispatcher during application lifespan. It claims jobs with database leases, builds a scoped internal request and awaits the same chat-completion handler. Output is stored as an ordinary conversation, preserving the existing tool cards, sources and artifacts. A browser refresh does not stop the worker.

## Execution modes

- **Chat:** existing conversation behavior and optional tools.
- **Agent:** explicit composer selection; multi-step native tool loop, schema validation, bounded parallel reads and approval before actions or unknown connectors. Known server-side read-only built-ins can run without repeated approval clicks. Tools impersonating built-in names do not inherit this exemption.
- **Background research:** `/agents`, persistent objectives, model selection, optional configured web research, adjustable execution-credit budget, activity history, pause/resume/cancel and explicit result verification. Read-only planner, researcher and verifier delegates run in the parent's lease and credit budget. Child agents cannot recursively delegate. Mutations, code execution, direct browser tools and external connectors remain unavailable in this mode.

## Persistence, budgets and recovery

Migration `d90ac81f2e10` adds `agent_run` and `agent_owner_lease`; it follows the existing joined authentication/billing/upstream migration head. Existing chat and user records are preserved. Account deletion removes owned runs and owner leases.

Defaults: four active jobs per process; at most one active job per owner across workers sharing the database; five submission attempts per owner per minute; 300-second task deadline; twelve tool iterations; 256,000 execution credits. Submission supports 30–3,600 seconds, 1–40 iterations and 4,096–500,000 credits. Existing plan restrictions and provider quota reservations still apply.

Execution credits conservatively reserve UTF-8 serialized model-input bytes plus overhead and an output allowance for every provider call. They are **not measured tokenizer usage, invoice amounts or a promised number of steps**. Generated output is capped at 2,048 tokens per call. Child research agents use the same budget. The UI distinguishes credit consumption from token billing.

Workers renew 60-second leases every five seconds and recheck active, verified authentication, session revocation and owner role. Credits and tool starts reject stale leases. An expired running lease becomes blocked rather than blindly replaying uncertain work. Pause cancels the running coroutine after acknowledgement; cancellation cannot undo an already-running remote request or synchronous plugin thread. Resume requires explicit owner action, is limited to three attempts, repairs interrupted read calls in the saved conversation and refuses outstanding unknown actions. A deadline includes queue time; a resume starts a fresh bounded time window while retaining consumed credits.

A completed model response becomes `needs_review`. Only explicit owner verification marks it `completed`; automatic proof of objective completion is not claimed. Specialist verification is available through delegation and produces evidence, not an infallible success signal.

## Tools, research and security

- Locally resolved JSON Schema contracts validate V2 non-MCP inputs and registered outputs; remote schema resolution is denied. MCP retains its SDK/server contracts. Sync plugins run outside the event loop.
- Independent known read tools run in groups of four. Unknown connectors, writes and direct tools form sequential barriers. Results retain provider ordering. Repeated identical failures are blocked; timeouts explicitly warn against blind action retries.
- `research_web` searches up to five distinct queries, concurrently searches three at a time, deduplicates source URLs and returns citation IDs and per-query errors. Source text remains untrusted input.
- Search caching is owner scoped, bounded to 128 entries with a 60-second TTL, joins identical in-flight requests and limits provider concurrency to sixteen. Every request rechecks entitlements. Search quotas remain charged even on cache hits. Cache contents are process-local; no cross-user sharing occurs.
- File search preserves source authorization and falls back to bounded lexical retrieval when semantic retrieval is unavailable. File attachments submitted to background runs must belong to the owner; shared-file attachments are currently rejected conservatively.
- Timelines contain operation metadata, not raw tool inputs or secret values. Compare-and-swap event sequence updates preserve concurrent events on SQLite and PostgreSQL. The latest 256 events are retained. SSE supports reconnect cursors; the UI uses incremental polling, avoids overlapping requests and pauses polling in hidden tabs.
- APIs require verified sessions and filter by owner on every history/control/event request. Run identifiers grant no authority. Existing configured sandbox/browser/code integrations remain required; no generated code executes directly on the application host.

## Configuration and operation

Install the repository's pinned backend dependencies (including `jsonschema==4.26.0`) and run the normal application startup/migration flow. No new broker, cloud account or production infrastructure is required. Use PostgreSQL with a shared database for multiple application workers. SQLite concurrency is covered by local regression tests; a PostgreSQL cluster/load benchmark has not been performed.

Existing model and search-provider settings remain authoritative. Background web research blocks with a configuration explanation when web search is disabled. Disable its checkbox for file-only or other supported read tasks. Administrative subagent settings control whether delegation tools are exposed. API submissions may attach up to twenty owned file IDs; the new background form does not yet include an upload picker.

`AGENT_TOOL_TIMEOUT_SECONDS` optionally overrides tool timeout budgets with a finite value from 1 to 1,800 seconds. Defaults remain 180 seconds, or 600 for built-in image tools; interactive questions, timers and delegation keep their existing wait semantics. A background task's outer deadline still bounds joined delegation.

## API

- `GET /api/v1/agent-runs/?since=<updated_at>`: up to 100 owner-scoped runs, optionally changed since a timestamp.
- `POST /api/v1/agent-runs/`: objective, model ID, owner-scoped idempotency request key and optional limits, web-search flag and file IDs. Changing an existing key's objective, capabilities or limits returns 409.
- `POST /api/v1/agent-runs/{id}/pause`, `/resume`, `/cancel`, `/verify`: owner controls.
- `GET /api/v1/agent-runs/{id}/events?after=<sequence>`: bounded SSE connection, ordered activity events and terminal state; reconnect using the last sequence. History is bounded, so clients should also refresh the snapshot.

## Validation and remaining work

See `AGENTIC_ENGINE_V2_VALIDATION.md` for executed checks and screenshots. Test providers and credentials used for browser validation live outside application code; no fixture response is installed in production paths.

This release does not claim the entire master specification is complete. Durable external actions with approval/recovery, a standalone isolated browser/computer runtime, newly provisioned execution sandboxes, automatic model fallbacks/cost routing, a generic dependency-DAG scheduler, a new distributed circuit-breaker service, complete OpenTelemetry spans and production-scale benchmarks remain outside this implementation. Existing interactive actions and configured integrations continue working through their established paths. Real provider, payment, email and connector credentials have not been exercised in local validation. No production infrastructure was deployed or changed.
