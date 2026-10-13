# ANSWERAI expanded vulnerability review — 2026-10-13

**Result:** four additional security failures were reproduced locally and patched: unverified-email linking through token exchange, stale administrator authorization in Socket.IO, document-state reads based only on room membership, and release-tag shell injection. The completed regression suite passes 82 backend tests and 9 frontend tests. Dependency and configuration risks remain.

This is an expanded repository review of baseline `7391df4`, supplementing [the initial review](SECURITY_AUDIT_2026-10-12.md). “Zero-day scan” describes the requested hunt; it does not establish that these flaws were previously unknown to vendors or researchers. No verified vendor zero-day discovery or vulnerability-free certification is claimed.

## Scope and limitations

- Whole-tree Semgrep run: 5,123 repository files considered, 364 applicable rules executed from security-audit, OWASP and secrets rule packs; Python, JS/TS, YAML, shell, Docker and generic patterns. Semgrep's “tracked by git” wording does not mean every line was semantically analyzed. Svelte sinks were additionally reviewed manually because generic matching is not a full Svelte security analyzer.
- AST route inventory: 607 HTTP/WebSocket declarations plus 15 Socket.IO handlers, across 39 Python files; 592 decorated functions, some with multiple routes. This is an inventory, not 622 independently penetration-tested endpoints.
- Bandit backend scan; npm lockfile audit; direct Python pins; Python 3.11/Linux-compatible exports of the application lockfile; separate resolution of the full backend requirements; and an audit of the installed test environment.
- Gitleaks scanned the Git history available in this checkout with 100% report redaction. The repository is **shallow**: older upstream history, other remote branches not present locally, external secrets and deployment infrastructure are outside this result.
- Manual review covered authentication/MFA/token exchange, OAuth claim trust, shared notes/chats/folders/skills/calendars/memories and access grants, Socket.IO/CRDT, terminal/live-call authorization, storage/cache/archives, browser HTML and message passing, SQL/execution sinks, outbound-fetch defenses, admin/billing/webhooks, Docker and publishing workflows. Dynamic reproductions focused on the four confirmed failures and selected boundary tests; this is not a full live deployment pentest.
- Final Semgrep run retained nine partial-parse diagnostics in Docker/release workflow shell fragments, Dockerfile and docker-compose-launcher.sh. Two files above the 1 MiB scanner limit and seven ignore-pattern matches were skipped. Earlier config.py rule timeouts were addressed by increasing the timeout; manual source review remains necessary for scanner gaps. Tests and scanners do not cover all runtime state combinations, optional ML/OCR integrations, all platforms, production proxies, real OAuth providers, live models or real payment transactions.

No production service, third-party system, real customer account, payment or secret was attacked. OAuth userinfo, Socket.IO transport and CRDT persistence were mocked at their boundaries; actual application controllers, token/auth database checks and CRDT encoding were exercised. Release tests execute only the tag-calculation shell block with benign temporary-file markers, never publish images or use registry credentials.

## Confirmed failures and remediation

### AAI-2026-101 — unverified email links an existing account through token exchange

**High, conditional account takeover/account linking.** The optional `/api/v1/auths/oauth/{provider}/token/exchange` endpoint is disabled by default. When it and email merging are enabled, a provider that returns an unverified address could supply another user's email and a different subject. The route linked that subject to the existing account and issued an app session in the local reproduction. Required MFA can limit immediate session issuance but does not justify an unverified link.

Affected code: [routers/auths.py](../backend/answerai/routers/auths.py), `token_exchange`, especially the account merge and domain allowlist. The initial fix covered the browser OAuth callback; this separate endpoint required its own review.

**Fix:** use the existing strict ownership-proof decision before email-based linking and restricted-domain admission. Positive boolean proof is accepted; false, absent, string and integer claims cannot silently count as proof. Previously configured provider trust exceptions still follow the shared policy. Existing subject-based login remains possible where applicable.

**Evidence:** before the fix, the local HTTP endpoint returned 200 and a victim-account JWT for a provider response with `email_verified=False`. After the fix it returns 403 and leaves the OAuth subject unlinked. Parameterized tests also verify valid proof still links successfully.

### AAI-2026-102 — Socket.IO uses a cached administrator role after demotion

**High, retained privilege after an authorized role change.** An administrator demoted to an ordinary verified user could retain the connection-time `admin` role in an already established Socket.IO session. The token resolver fetched the current user, but `get_socket_session_user` discarded that result and returned the stale snapshot. Handlers relying on the returned role could continue bypassing note/resource checks.

Affected code: [socket/main.py](../backend/answerai/socket/main.py), `get_socket_session_user` and callers.

**Fix:** return the currently verified database-backed user fields, with the same sensitive/profile-field exclusions. Invalid or revoked sessions retain the existing disconnect behavior.

**Evidence:** the real auth/database-backed local test demotes an admin while retaining a valid session token. Before the fix the resolver returned `admin`; after it returns `user`. This is retained prior privilege, not ordinary-user self-promotion.

### AAI-2026-103 — existing document room permits state reads without current authorization

**Medium, potentially confidential document disclosure.** `ydoc:document:state` checked room membership but did not check current session validity or note read access. A previously authorized session left in a room after a role/access change could read CRDT state despite losing permission.

Affected code: [socket/main.py](../backend/answerai/socket/main.py), `yjs_document_state`.

**Fix:** validate the current session and recheck notes permission, note existence and ownership/read grants before retrieving state. Room membership remains required but no longer substitutes for authorization. Authentication failure schedules disconnect safely while the document lock is held.

**Evidence:** before the fix the handler fetched state for a demoted non-owner already in a simulated room. After it, no state is read or emitted. The same test verifies a current administrator can still read valid CRDT-encoded content, preventing an accidental deny-all implementation.

### AAI-2026-104 — release Git tag becomes shell source

**Medium, CI command execution; requires tag-push privileges.** Docker publishing embedded `${{ github.ref_name }}` directly in a Bash program. A Git-valid tag containing command substitution executed a harmless marker command in the local extracted-script reproduction. This is relevant where tag-push permission is less restricted than protected release branches; it is not an unauthenticated pull-request exploit. An affected live job has registry credentials and package-write permissions, but no real credential exposure was attempted.

Affected code: [.github/workflows/docker.yaml](../.github/workflows/docker.yaml), Docker Hub tag calculation/copy and image inspection.

**Fix:** read refs from quoted runtime environment variables; reject invalid Docker release versions; pass derived tags/image versions as environment data instead of substituting them into shell source. Normal release/prerelease tags remain supported.

**Evidence:** before the fix a valid specially named Git ref created a local marker. After the fix it creates no marker and is rejected. Tests also execute valid release-tag cases; Semgrep no longer reports the two original release-shell-injection matches.

Regression source: [backend/tests/test_dayzero_review.py](../backend/tests/test_dayzero_review.py). The four initial reproduction tests failed for the security expectation at baseline, then passed after remediation. The test file now has 22 cases, including additional SSRF/archive/release boundary checks. CI runs these with the existing authentication/billing/security tests.

## Scanner results and dependency scopes

Counts are scanner entries, not independent remotely exploitable vulnerabilities. They include transitive parents, advisory aliases, heuristics and hardening suggestions. **Do not add the different Python scan totals:** their package sets overlap and resolve differently.

| Scan                                             | Result                                                                                             |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Semgrep, initial whole tree                      | 89 findings: 23 ERROR, 61 WARNING, 5 MEDIUM; 12 diagnostics                                        |
| Semgrep, follow-up                               | 85 findings: 21 ERROR, 59 WARNING, 5 MEDIUM; 9 partial-parse diagnostics                           |
| Bandit, backend                                  | 205 findings: 51 medium, 154 low, no high                                                          |
| Gitleaks, available history                      | No leaks found; shallow-history limitation applies                                                 |
| npm, including development tools                 | 43 affected-package entries: 2 critical, 11 high, 20 moderate, 10 low                              |
| Direct full-backend Python pins                  | 12 advisory entries in 6 packages                                                                  |
| Compatible application-lock export               | 34 entries in 16 packages before updates; **16 in 9** afterward, 256 evaluated distributions       |
| Independently resolved full-backend requirements | 14 entries in 8 packages, 333 evaluated distributions                                              |
| Installed isolated test environment              | No known advisories at scan time; 118 distributions evaluated after the fixed-version test install |

Targeted lockfile updates: anyio 4.14.2, h2 4.4.1, hpack 4.2.0, multidict 6.9.1, pyasn1 0.6.4, soupsieve 2.9, urllib3 2.8.0. The regression environment was aligned to these versions. A clean installed test environment does **not** mean the full production environment is clean: it excludes many optional production packages.

A newly resolved requirements installation does not exactly match `uv.lock`. For example, datasets/unstructured advisories occur in the full-requirements resolution while oauthlib/setuptools/torch entries occur in the compatible lock export. Audit the actual production artifact, selected extras, Python version, architecture and container image before deployment. No container OS vulnerability database scan or production image build was performed in this review.

Machine-readable, credential-free result summary: [security/2026-10-13-summary.json](security/2026-10-13-summary.json).

## Unresolved risks and triage

1. **Known dependency advisories remain.** Critical npm entries affect Vitest/tinypool development tooling; high chains include Vite/static-copy, Cypress and native sharp via frontend ML libraries. Do not expose development/test UI servers. Major toolchain upgrades and unsupported native dependency chains require integration validation. Remaining Python advisories across the overlapping scopes include accelerate, chromadb, datasets, fsspec, oauthlib, pyarrow, sentence-transformers, setuptools, torch, transformers and unstructured. The structured summary includes versions, IDs and reported fixed releases. Chroma/Accelerate entries currently have no reported fixed release. ML/model/document upgrades were not blindly forced.
2. **Recoverable API keys at rest:** `models/users.py`, `ApiKey.key`, stores plaintext bearer keys. Protect database/backups. A keyed-digest lookup plus one-time display/rotation migration is still needed; this is not evidence of remote database compromise.
3. **Host-privileged plugins and default-root containers:** `utils/plugin.py` deliberately executes Python; the prior admin policy restricts authoring but provides no execution sandbox. Dockerfile defaults `UID=0/GID=0`. Trusted extension authors and a least-privileged deployment account are required. Full plugin/ML isolation is unresolved.
4. **Remaining scanner patterns need context:** SQL text warnings examined in chats/migrations/pgvector used bound values or controlled names/enums; no SQL injection was confirmed in those paths. Raw-HTML warnings examined built model prompts or escaped attributes, not unsanitized browser HTML. Remaining logger warnings include token-count labels, session identifiers and provider error text; no raw bearer credential leak was confirmed by this scan, but arbitrary provider/exception text is not reliably redacted.
5. **Unverified JWT decoding:** back-channel logout reads an issuer for provider selection and subsequently verifies signature/audience/issuer before acting; stored ID-token decoding is used for refresh timing. Token-exchange claim fallback follows provider userinfo acceptance. The scanner patterns alone did not establish a forged-token acceptance path. Real-provider claim/audience behavior remains deployment-specific.
6. **XML hardening:** the YouTube `ParseError` import is not a parser invocation. Yandex does parse external/provider XML with ElementTree; no external-entity filesystem/network exploit was reproduced. A hardened parser and strict response-size bounds are recommended for hostile-response defense.
7. **Supply-chain/configuration hardening:** 37 mutable-action-tag matches, four Dependabot cooldown suggestions and one npm minimum-release-age suggestion remain. No compromised action was found; pin reviewed actions to immutable commits. Explicit TLS/cookie/proxy and local-web-fetch settings must be reviewed in the actual deployment. Disabling TLS validation, exposing trusted-header authentication directly, or enabling private-address fetching changes the trust boundary.
8. **Browser message passing:** Pyodide's opaque-origin iframe requires wildcard postMessage delivery; receivers check the sending window. No message-source bypass was confirmed. Existing Markdown/notebook/office/diagram HTML sinks examined use sanitization or the hardened iframe policy; this review does not certify every browser/parser edge case.

## Reproduce and deploy

Use supported Node 22 and isolated scanner tools. Run [scripts/security-review.sh](../scripts/security-review.sh) with an optional absolute report directory. It performs source scans, a redacted available-history scan, direct/locked/resolved dependency audits, records provenance and never calls a deployed platform. It returns 1 for findings or scan errors, and 2 for missing tools. Review individual logs; exit 0 is not a security certification. Scanner versions used here: Semgrep 1.180.0, Bandit 1.9.4, pip-audit 2.10.1, Gitleaks 8.24.3.

Validation: 82 backend tests; 9 frontend tests; backend compilation; new-test Ruff/Black; workflow shell blocks exercised with malicious/valid tag cases; shell syntax and branding audit. Frontend source was unchanged in this follow-up; the production build passed in the preceding change and was not unnecessarily repeated.

The changes extend [PR #3](https://github.com/aditya-gaharawar/answerai/pull/3). Deploy through normal review/migration procedures; this follow-up adds no database migration. Rebuild/reinstall using the updated lockfile rather than assuming a running environment automatically receives its transitive fixes.
