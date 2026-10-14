# ANSWERAI repository security rescan — 13 October 2026

**Historical scan:** two additional security issues were reproduced locally on merged commit `362350c5e0da8438c6b0fc8c2a3ff2a8efee35d2`.\*\* These are application authorization and resource-limit failures. Their novelty outside this repository has not been established; neither is claimed as a verified vendor zero-day. The subsequent 14 October repair fixes both findings; see [the system repair report](SYSTEM_REVIEW_2026-10-14.md). The evidence below records the pre-fix behavior.

## Findings

### AAI-2026-105 — optional provider passthrough bypasses billing authorization

**High, conditional. CWE-862 / CWE-863.** Requires an authenticated ordinary user and `ENABLE_OPENAI_API_PASSTHROUGH=True` (disabled by default). The provider connection's credentials and upstream permissions determine the ultimate impact.

Affected code:

- [utils/plans.py](../backend/answerai/utils/plans.py): `enforce_http`, especially the POST/PUT/PATCH outer guard, suffix allowlist at line 271 and exact generation paths at line 276.
- [routers/openai.py](../backend/answerai/routers/openai.py): `proxy`, line 1919 onward, forwards requests with the configured provider credential without resource ownership/model authorization.

Two paths reach the same unchecked proxy:

1. GET and DELETE never enter the billing guard. An ordinary user can dispatch provider file-content reads or deletions using the application's provider credential. There is no application-level per-user ownership check on these resources. This can expose or delete shared provider-project resources where the credential permits it; the local test proves forwarding, not a real provider deletion.
2. POST paths ending in `/chat/completions` or `/responses` pass the suffix allowlist, but only exact paths reserve generation usage. Encoded dot segments are decoded by ASGI routing and subsequently normalized by the outbound client's URL library. A noncanonical path therefore reaches the provider's canonical generation endpoint without checking the requested model or reserving quota. Reverse proxies that reject or normalize these paths can affect this particular route; they do not repair the GET/DELETE issue.

**Local evidence:** all four cases returned HTTP 200 through the real verified-user dependency and database billing policy despite a free account with zero message/request limits and a model allowlist excluding the supplied model. The extracted, unchanged proxy controller called a mocked provider with a fake server credential. The outbound URL normalization was checked using the installed `yarl` library used by aiohttp. Canonical POST generation and file-management control requests were denied with 403.

**Recommended fix:** make the generic provider proxy administrator-only, or implement explicit per-method, per-endpoint authorization with provider-resource ownership mapping. Apply policy to every HTTP method, reject noncanonical path segments, use exact allowlists, and enforce model/quota checks at the outbound dispatch boundary. Retaining the default disabled passthrough setting mitigates this finding.

### AAI-2026-106 — speech generation bypasses the plan request limit

**Medium. CWE-770 / CWE-799.** Requires an authenticated ordinary user with `chat.tts` permission and an OpenAI speech connection. Does not require generic passthrough to be enabled.

Affected code: [routers/openai.py](../backend/answerai/routers/openai.py), `speech`, lines 517–555; [utils/plans.py](../backend/answerai/utils/plans.py), `enforce_http`. `/openai/audio/speech` is explicitly permitted, but it is absent from generation reservations and feature quota dispatch. The controller checks TTS permission and then calls the paid provider without a plan request reservation.

**Local evidence:** with billing enabled and `requests_per_minute=0`, the real extracted speech controller made a mocked provider call, wrote synthetic audio to a temporary cache and returned HTTP 200. The expected 403/429 did not occur. Unique input bodies avoid the existing cache, permitting repeated provider work and cache growth. Upstream rate limits may bound the abuse; local plan limits currently do not. No real provider usage or charges were generated.

**Recommended fix:** add an explicit speech entitlement/budget, reserve the plan request counter before provider dispatch, and cap input size, concurrent requests and cache retention. Apply the same policy to other speech/transcription entry points after checking their intended billing semantics. Restricting TTS permission is an interim mitigation. A chat-model allowlist should not be reused for speech without defining how speech models are configured.

## Fresh automated scans

The committed `scripts/security-review.sh` was rerun against the merged baseline. Its exit status was 1 because it found issues; individual scanner outputs were inspected.

| Scanner / scope                                        | Result                                                                                             |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Semgrep 1.180.0                                        | 85 findings: 21 ERROR, 59 WARNING, 5 MEDIUM; 364 rules; 5,126 targets; 9 partial-parse diagnostics |
| Bandit 1.9.4                                           | 205 findings: 51 medium, 154 low, no high                                                          |
| npm audit, including development dependencies          | 43 package entries: 2 critical, 11 high, 20 moderate, 10 low                                       |
| pip-audit 2.10.1, direct backend requirements          | 12 advisory entries in 6 of 115 distributions                                                      |
| pip-audit, compatible application lock export          | 16 advisory entries in 9 of 256 distributions                                                      |
| pip-audit, independently resolved backend requirements | 14 advisory entries in 8 of 333 distributions                                                      |
| Gitleaks 8.24.3, available Git history                 | No leaks found across 13 commits / approximately 45.35 MB; checkout is shallow                     |

These are scanner/advisory entries, not counts of confirmed exploitable application flaws. Python scopes overlap and must not be summed. The npm critical entries concern development tooling; production exposure requires separate assessment. Known dependency, plaintext API-key storage and privileged plugin/container risks remain described in the [earlier review](SECURITY_REVIEW_2026-10-13.md). They are not newly discovered issues in this rescan.

Machine-readable summary: [security/2026-10-13-rescan-summary.json](security/2026-10-13-rescan-summary.json). Raw local output is in `/workspace/answerai-rescan-20261013`; it was not published to an external service.

## Reproduction and limits

The local evidence is in [test_security_rescan.py](../backend/tests/test_security_rescan.py). Install `backend/tests/requirements.txt` in an isolated Python environment and run:

```sh
python -m pytest backend/tests/test_security_rescan.py --runxfail -q --tb=short
```

On the affected baseline, five security expectations fail with **actual HTTP 200 responses**, while two control tests pass. The original five cases carried strict expected-failure markers. The 14 October repair removes those markers, expands coverage, and makes these expectations pass.

Combined validation with the existing authentication, billing and security suites: **84 passed, 5 expected failures**. That was the pre-repair validation; the subsequent repair includes production changes and separate validation.

Provider networks and secrets are mocked, identity resolution is supplied by the existing test fixture, and actual billing configuration, user rows, verified-user policy, controller bodies, ASGI routing and temporary file writes are exercised. Controllers are AST-loaded because the minimal test environment excludes optional ML SDKs. This does not test full production middleware/proxies or prove upstream acceptance by every provider. No customer resources or third-party endpoints were attacked.

Whole-tree scanners include heuristic false positives. Semgrep skipped two files above 1 MiB and seven ignore-pattern matches; Svelte and complex framework dataflows are not exhaustively analyzed. No deployed-service penetration test, container OS scan, older unavailable Git history review or guarantee of complete vulnerability coverage is implied. The previous four reproduced fixes remain in the merged baseline.
