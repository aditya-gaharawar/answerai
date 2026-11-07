# Usage limits and admin resets

Configure limits in **Admin settings → Plans, payments & live calls**. Enforcement must be enabled for non-admin plan limits to apply. Existing account blocking and model restrictions continue to apply independently. Admin accounts bypass plan quotas.

Each Free/Plus plan supports messages per day, per five hours and per week; token credits per day, per five hours and per week; requests per minute; daily feature/audio/live budgets; and a maximum response allowance. New window/token limits default to unlimited (`null`) so existing installations retain their limits until an administrator configures them. Zero prevents usage; clearing a new limit removes that limit. All active budgets must allow a request.

Five-hour (18,000 seconds) and weekly (604,800 seconds) windows start when the account first consumes that window. They reset on the first use after expiry. They are anchored windows, not sliding-lookback averages. Daily/minute budgets keep their UTC boundaries. API responses expose active usage, limits, remaining credits and reset timestamps. Quota rejections include `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining` and `X-RateLimit-Reset`.

## Token credits

Credits are conservative admission reservations, not a provider invoice or an exact provider tokenizer count. Each generation reserves UTF-8 bytes of serialized input fields, 1,024 overhead credits, and its output allowance. When token budgets are enabled, the response allowance is capped at the configured maximum. Provider OpenAI/Responses and Ollama proxies reapply the cap after model defaults. Their first provider call uses the admission reservation, topping up for expanded input; subsequent agent/tool provider calls reserve additional credits. Cancellation, upstream failure and shorter responses do not refund the reservation. Multimodal/provider-specific costs do not correspond to these text credits. Plugins/direct client connections have their own execution paths and do not report server-provider follow-up usage.

This avoids trusting client-supplied usage and permits rejection before remote generation. The counters do not require a provider response to arrive successfully.

## Reset controls

Enter a user ID/email and choose **View user usage**. Select either **Selected user** or **All users (global reset)**, enter a reason and type `RESET`. The global option restores quota availability for every account. Resetting removes rate/feature/token counters and the anchored-window state, so the next use starts fresh windows. It does not change account plans, subscriptions, payments, checkout/payment-management abuse counters, login/MFA limiters, or active-call leases. In-flight precharged requests can finish; later provider calls reserve against the new counters.

Admin-only endpoints:

- `POST /api/v1/billing/users/{id-or-email}/usage/reset`
- `POST /api/v1/billing/usage/reset`

Both accept `{"reason":"Support adjustment","confirmation":"RESET"}`. Counter deletion and the audit record commit in the same transaction. The response reports scope and counter rows removed. Existing administrator authentication controls also protect these routes.

## Concurrency and efficiency

Reservations use conditional database updates and unique keys, with bounded conflict retries; all budgets within a reservation succeed together or roll back together. Anchors are shared by message/token metrics in the same window. No process-local quota cache needs invalidation after resets. Generation resolves entitlements once for its feature/model checks. Expired counters are cleaned only when a new bucket is created, scoped to that user, instead of a global delete on every request. No database schema migration or Redis service is required.

## Verification

208 backend tests and 101 frontend tests passed. Strict Svelte/TypeScript diagnostics report zero errors/warnings; production build, Python formatting/fatal correctness and branding checks passed. A browser fixture verified viewing user usage, the global warning/confirmation, the reset payload/result and clearing confirmation after success. [Admin reset screenshot](screenshots/quota-controls/admin-global-reset.png). Live provider billing was not exercised.
