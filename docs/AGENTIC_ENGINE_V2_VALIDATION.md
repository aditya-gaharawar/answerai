# Agentic Engine V2 validation

Verification session: 2026-11-08 (Asia/Calcutta; logs use UTC). Local Linux workspace, Python 3.12, Node 22, Chromium. No production deployment or paid provider credentials were used.

## Executed checks

| Check                                                                            | Result                                                                                           |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Backend regression suite                                                         | 243 passed, 15 warnings, 59.69 seconds in the final aggregate run.                               |
| Frontend unit suite                                                              | 101 passed across 43 files                                                                       |
| Strict Svelte/TypeScript check                                                   | Zero errors and zero warnings                                                                    |
| Production build                                                                 | Passed with Node 22 and a 6 GiB V8 heap cap; SSR build 14.15 seconds, client build 21.45 seconds |
| Ruff syntax/name checks and formatting                                           | Passed on changed backend modules                                                                |
| Branding audit                                                                   | Passed; 5,413 text files, with upstream branding retained only in legal notices                  |
| Browser → API → database → worker → streaming provider → tool → persisted result | Passed using a separate deterministic local OpenAI protocol fixture                              |
| Browser refresh                                                                  | Persisted execution and tool events retained                                                     |
| Explicit verification                                                            | `needs_review` changed to `completed` through the authenticated API                              |
| Mobile layout                                                                    | Passed at 390 × 844; no horizontal document overflow                                             |
| Browser errors                                                                   | Zero uncaught page errors                                                                        |

An initial production build was killed when it competed with the development compiler and browser for memory. The isolated rerun completed successfully. Existing backend warnings concern pytest fixture-loop defaults, upstream ASN.1 deprecations and historical SQLite migration primary-key definitions; tests still passed.

The browser task requested the current timestamp. The provider fixture emitted a streamed `get_current_timestamp` call; the **real application tool** executed, the provider received its result, and the subsequent answer was persisted. The fixture itself supplies test text and synthetic usage. It does not establish live-model reasoning quality, actual token prices, search-provider reliability or real connector behavior. No fixture is registered in application startup or production provider routing.

Execution regression tests cover owner isolation, idempotency and conflict rejection, eight competing worker claims with one winner, lease fencing, worker crash blocking, bounded resume, atomic credit reservations, ordered streaming replay, twelve concurrent timeline writes without lost events, per-owner scheduling fairness, cache single-flight/isolation/capacity, read-only delegation restrictions, schema-reference denial, safe-read approval exemptions and incomplete specialist responses remaining blocked.

## Screenshots

- [Desktop activity and tool execution](screenshots/agentic-v2/desktop.png)
- [Mobile execution history](screenshots/agentic-v2/mobile.png)

Screenshots use a local validation account and model; they contain no production user data or credentials.

## Reproducing browser verification

Use an isolated test database and local/staging application, with a verified test account. Install the normal backend/frontend dependencies, and use Node 22. A deterministic test provider is available through:

```sh
python -m uvicorn --app-dir backend/tests/fixtures agentic_provider:app --host 127.0.0.1 --port 8190
```

In the **test application's** provider settings, add `http://127.0.0.1:8190/v1` with a placeholder test key. Confirm `agent-validation` appears in model discovery. Disable web search for the smoke task. Do not register this fixture in production.

Install Playwright in a disposable directory if it is not already available, and set `NODE_PATH` to that directory's `node_modules`. Supply `AAI_TEST_BASE_URL`, `AAI_TEST_TOKEN` and `AAI_TEST_MODEL=agent-validation` through the environment. Optionally set `CHROMIUM_PATH` and `AAI_TEST_ARTIFACTS`. Then run:

```sh
node scripts/verification/agentic-v2-browser.cjs
```

The script creates a real task/conversation, verifies its persisted tool event after refresh, explicitly confirms its result and writes desktop/mobile screenshots. It never prints the authentication token.

For normal suites:

```sh
PYTHONPATH=backend python -m pytest backend/tests -q
npm run test:frontend
npm run check
NODE_OPTIONS=--max-old-space-size=6144 npm run build
```

## Limits of the evidence

No PostgreSQL cluster/load test, worker-host kill benchmark, live paid-model evaluation, connector/OAuth integration test or production search benchmark was performed. Crash recovery is exercised through database lease expiration and interrupted state in regression tests. The smoke fixture validates transport and state transitions, not the full breadth of the master specification. See [architecture and remaining capabilities](AGENTIC_ENGINE_V2.md).
