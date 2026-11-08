# Chat tool flow improvements

Agent-mode requests now put relevant authorized tools first using the latest user message and attached-file context. The selector does not treat retrieved content or an assistant message as authority, does not grant permissions, and caps promotions at eight tools. With administrator-enabled tool discovery, relevant deferred schemas are loaded directly, saving discovery round trips while leaving other tools searchable. When discovery is disabled, tool ordering still applies; schema pruning is not forced over the administrator's setting. These keyword hints supplement model selection; they are not a multilingual intent classifier.

Parallel read batches join identical calls with equivalent JSON arguments. This optimization lasts only within a contiguous batch. Writes, unknown connectors and direct tools remain ordered barriers; a read after an action executes again. Successful result payloads remain compatible with existing file/image/source handlers. Each call retains a provider result, with separate mutable result data. Existing user-scoped web caching and research concurrency remain in place.

Agent tool errors gain `ok: false`, an error category, retryability and recovery guidance. Explicit non-retryable errors stay non-retryable. Actions default to state inspection before another attempt; read failures suggest changing the query or source. This is model guidance, not automatic action replay. Validation and existing failure guards continue to apply. Successful outputs are not wrapped into a new envelope that could break image rendering or artifacts.

Chat tool cards now describe common work in plain language, such as searching the web, reading files and generating images. Failed calls are explicitly labeled. Exact tool identity, arguments, results and approval controls remain inspectable. The agent instructions favor direct execution for simple requests, independent read batches, evidence reuse and concise final results. They do not instruct models to skip necessary verification.

Each executed tool logs its name, kind, elapsed time and success/failure without argument values. Existing provider observability can be used alongside these timings. No provider latency reduction or task-quality improvement is claimed without live-provider evaluation.

## Validation

Regression tests cover user-context selection, authorization-preserving availability, equivalent JSON read deduplication, action barriers, connector name collisions, mutable-result isolation and recovery hints. The frontend label mapping is tested. Full-suite results are recorded in the accompanying delivery evidence.

A local simulated-I/O check with four independent reads measured 103.52 ms sequentially and 25.51 ms through the existing parallel dispatcher (4.06×). This demonstrates bounded batching behavior against a sequential baseline; it does not compare with the previous branch implementation, which already supported parallel reads, and it does not measure a real model/search provider. New duplicate suppression separately reduces equivalent read invocations within one batch, verified by regression tests.

Real provider/model comparisons, new persistent file-index caches and automatic model routing remain unmeasured or outside this change. Image, file, permission and conversation formats continue to use their established paths.

Local validation on 2026-11-08: 247 backend tests, 102 frontend tests, zero strict Svelte errors/warnings, production build, Python format/name checks and browser smoke all passed. Browser smoke used the separate local protocol fixture and exercised actual tool execution and persistence; paid providers were not used.
