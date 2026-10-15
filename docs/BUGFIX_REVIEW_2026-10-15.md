# Bug fixes and remaining work: 15 October 2026

This review follows upstream integration commit `829eefccf`. It repairs concrete failures found while checking the combined ANSWERAI application. It is not a claim that every defect or previously unknown vulnerability has been found.

## Repairs

- Audio uploads now pass the same speech permission and daily audio budget checks as direct transcription. A request marker prevents the HTTP route from charging twice. Blocked accounts remain blocked when billing is disabled.
- Local and downloaded embedding/reranking snapshots are checked before loading: checkpoint indexes have a size limit, shard paths cannot traverse outside the snapshot, and special files such as FIFOs are rejected. Legitimate Hugging Face cache blob symlinks remain supported. Failed snapshot downloads fail closed; the model constructors use local files only.
- The local `sprintf-js` compatibility patch limits malicious width, precision, format length, output length and parser-cache growth. The npm override applies it to transitive consumers; Docker copies the local package before installation. Its version identifies an ANSWERAI patch, not an upstream release. The original license is retained under `vendor/sprintf-js`.
- Copying an editor selection now serializes only that selection. Previously the copy handler serialized the entire editor document. Empty first lines in inserted text no longer attempt to create invalid empty ProseMirror text nodes.
- Notes discard stale loads and uploads after switching notes. HEIC conversion rejects normally instead of hanging inside an asynchronous Promise executor. Attachment image events use `CustomEvent.detail`; editor and textarea cleanup cancels pending work.
- List dragging handles both ProseMirror nodes and node types and removes window listeners on cancellation/destruction. Map selectors dispose late loads and render marker labels as text instead of interpreting HTML.
- Chat history traversal stops on cycles, handles missing children and accepts prototype-like message IDs. Prompt/chat variable maps also handle prototype-like keys; required fields preserve valid `false` and `0` answers.
- Direct model responses are validated and normalized. Sparse connection configuration no longer shifts responses onto the wrong connection. Google Drive OAuth refreshes expired credentials and loads the identity SDK even when the Picker SDK has already created the global object. Authorization debug logging was removed.
- AUTOMATIC1111 authentication accepts its documented username/password dictionary as well as a credential string; invalid shapes produce a controlled validation error. Administrator image/workflow settings use stable loaded configuration and validated file input.
- Added API/editor/SDK type contracts, repaired undefined references, corrected the virtual-list height/item-height props, fixed the embed parameter declaration that broke development dependency scanning, and corrected a global CSS selector that the CSS compiler rejected.

## Verification

- Backend regression suite: 133 passed, covering authentication/email verification, billing, payment validation, live providers, access controls, migrations and security cases. The snapshot helper was also retested after its internal refactor: 13 passed.
- Frontend regression suite: 36 tests passed across 11 files, including editor selection privacy, prompt variables, OAuth expiry, history cycles, source IDs, direct model responses and bounded formatting.
- Production build passed on Node 22 with `USE_SLIM=true`; this skips optional Pyodide package downloads. It does not exercise every optional ML integration.
- Production browser smoke passed with mocked APIs: administrator policy save, account lookup and reason gating; read-only note loading/permissions, note unmount, and chat editor input. Editable collaborative note synchronization was not exercised because the mock server does not implement Socket.IO.
- Branding audit passed. New snapshot code and modified billing/system regression files pass Ruff.
- Clean npm installation of the local formatter dependency was checked. npm audit reported zero advisories in the resolved JavaScript dependency tree. This does not certify application security or Python dependencies.

## Remaining issues

The full strict Svelte/TypeScript check still fails. The starting integration had 4,207 errors and 194 warnings. The latest check reports 3,095 errors and 194 warnings across 267 files: the error count has fallen by 1,112 without disabling strict checking or excluding application files. The remaining diagnostics include chat/call components, root layout, sidebar/search, response rendering and utility contracts. Build success does not make these diagnostics disappear; they still require continued repair.

The Python dependency audit still reports Accelerate and ChromaDB advisories without fixed versions in the audit data. Snapshot validation mitigates the documented Accelerate checkpoint path/FIFO attack at this application's embedding/reranking entry points; it does not patch every possible use of Accelerate or protect against a hostile local process modifying files during model loading. Chroma's native server authentication/RBAC and remote embedding code vulnerabilities are not fixed by this change. ANSWERAI uses an embedded client or a configured HTTP client with embedding functions disabled; an independently deployed Chroma server requires its own remediation and isolation.

Real email delivery, payment settlement, microphone/camera calls against OpenAI/Gemini, and large optional ML model loading were not tested against paid services. Their regression tests use mocks.
