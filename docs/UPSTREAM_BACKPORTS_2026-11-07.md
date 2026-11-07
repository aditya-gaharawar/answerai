# Upstream backports — 7 November 2026

> Historical backport stage, superseded by the [complete upstream merge](UPSTREAM_FULL_MERGE_2026-11-07.md). The integration now includes upstream main 0.13.0 with real merge ancestry.

Compared upstream main `c38885a1a737da4968f157092f304f3b5481d0bf` (0.13.0) with the previously integrated `91ea4e3421d1d8069f13d4a463fcb5986d94ea60` (0.12.3). Upstream has 679 additional commits and changes 673 files. A trial full merge produced 233 conflicted paths and was aborted. This branch backports the eight changes below; it does **not** claim the full 0.13.0 release or record unintegrated upstream ancestry as merged.

| Upstream commit | Behavior brought into ANSWERAI                                                                                    |
| --------------- | ----------------------------------------------------------------------------------------------------------------- |
| `4adf3083f3`    | Detect ZIP document archives by contents, so renaming an archive cannot bypass decompression-size checks.         |
| `b4b6cc936d`    | Recheck the current account and knowledge read grant after each pending-files streaming poll.                     |
| `dd6720c528`    | Preserve non-ASCII stop sequences while continuing to decode escaped newlines for OpenAI and Ollama.              |
| `aa1326eaea`    | Keep provider usage and partial output when a Responses API stream ends as incomplete.                            |
| `1d5373066d`    | Avoid creating a telemetry series for each unmatched raw request URL.                                             |
| `97f5c4e973`    | Clear folder links when archiving all chats, preventing later folder deletion from deleting those archived chats. |
| `aec5796a53`    | Forward Preview callbacks through nested Markdown lists, quotes and details blocks.                               |
| `47934d1cc2`    | Keep terminal policy fields that the connection editor does not expose.                                           |

All changes were applied with their upstream context. The knowledge router's import hunk was adapted to the current ANSWERAI imports. Backend package names use `answerai`.

## Preservation and validation

Billing and payment handling, email verification, quota enforcement, live-call providers, connector implementation, admin controls and encryption artifacts remain unchanged. The existing UI design and framework/dependency configuration remain in place.

- Existing backend suite: 196 passed.
- New regression suite: seven passed, covering Unicode and escaped stops for both providers, incomplete-response usage, mid-stream knowledge-access revocation, and oversized ZIP files under three misleading filenames.
- Strict frontend diagnostics: zero errors and warnings. All 98 frontend tests across 42 files passed. The production build, encryption source/checksum verification and actual WASM round-trip smoke passed.
- Branding and fatal Python correctness checks passed; all modified Python files pass formatting checks.

The remaining 0.13.0 agent/sub-agent functionality, side panels, notifications and other changes require further integration and testing. The unresolved full merge has not been published or deployed. Real SMTP, payments, external OAuth and AI-provider calls were not exercised with production credentials.
