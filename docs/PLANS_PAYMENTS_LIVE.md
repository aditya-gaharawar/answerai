# Plans, payments, and the current call feature

Open **Settings → Admin → Plans, payments & live calls**. Changes apply on the server; refresh the app to update model lists and permission controls.

## Plans and restrictions

Plan enforcement starts **disabled**, preserving existing accounts. Configure Free and Plus before enabling it. Defaults are starting values, not published product pricing:

| Setting | Free | Plus |
| --- | --- | --- |
| Generation requests/day | 20 | 1000 |
| Requests/minute | 5 | 60 |
| Live minutes/day | 0 | 60 |
| Maximum call length | 15 minutes | 30 minutes |
| Features | Uploads | All listed features except direct connections |
| Daily feature operations | 10 uploads | 100 per enabled feature |

Generation requests count attempted model generations, including direct provider APIs. A single application generation is reserved once across internal dispatch; a separate server task using the same request shares that reservation. Daily limits reset at midnight UTC; minute limits reset on clock-minute boundaries. Zero denies usage. Counters are atomically stored in the application database, shared by workers, and survive restarts. Database failures do not bypass enforcement. Invalid or unsuccessful provider requests may consume a reservation.

Features: uploads, images, web search, code execution, tools/integrations, memory, automations, live calls, camera input, and direct connections. Limits are additional to existing group permissions and model sharing; purchasing Plus does not grant access to a privately shared model. Model IDs are exact, with `*` allowing all shared models. A custom model and its base model must both be allowed. For voice model restrictions, add e.g. `live:openai/gpt-realtime` or `live:gemini/YOUR_GEMINI_MODEL`.

Administrators bypass plan quotas. Individual account overrides can force Free, grant Plus, or block generation and paid features, optionally until an expiry. The billing page remains accessible. Overrides do not cancel billing; cancel the provider subscription separately when needed. Returning an override to Automatic uses confirmed subscription access or Free. Direct OpenAI passthrough is blocked for non-admin users while plan enforcement is on, because arbitrary provider endpoints cannot be safely metered.

## Stripe

1. Create a recurring, fixed per-unit Price in Stripe. Configure the customer portal in Stripe if you want customers to manage payment methods and invoices.
2. Put these secrets in the server environment or root `.env`, then restart:
   ```dotenv
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_WEBHOOK_SECRET=your_endpoint_signing_secret
   ```
3. Add a webhook at `https://answerai.in/api/v1/billing/webhooks/stripe`. Subscribe to `checkout.session.completed`, `checkout.session.expired`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated`, `customer.subscription.deleted`, and `charge.refunded`.
4. Enter the recurring Price ID in ANSWERAI's admin settings, set the public URL, and enable Stripe. Checkout displays the actual price, currency, and billing interval fetched from Stripe. The REST client uses API version `2024-06-20`; use the same webhook version where possible.

Checkout is hosted by Stripe. Paid access requires the current subscription's latest invoice to be paid, the server-configured Price ID, one unit, and an active subscription. Full refunds of the current invoice revoke access. A scheduled cancellation retains access through the paid period; immediate cancellation or failed billing revokes access when the webhook is processed. Webhook timestamps have a five-minute signature tolerance. The portal and cancellation endpoints verify ownership.

## Razorpay

1. Create a Razorpay recurring Plan and enable Subscriptions for your merchant account.
2. Set and restart:
   ```dotenv
   RAZORPAY_KEY_ID=your_razorpay_key_id
   RAZORPAY_KEY_SECRET=your_razorpay_key_secret
   RAZORPAY_WEBHOOK_SECRET=your_endpoint_signing_secret
   ```
3. Add `https://answerai.in/api/v1/billing/webhooks/razorpay` with that signing secret. Enable subscription events, especially `subscription.charged`, `subscription.activated`, `subscription.pending`, `subscription.halted`, `subscription.cancelled`, `subscription.completed`, and `refund.processed`.
4. Enter the Plan ID and enable Razorpay. The billing page loads Razorpay Checkout directly from `checkout.razorpay.com` only when chosen. Its public Key ID is sent to the browser; its secret is never sent.

A checkout callback does not grant access. Signed subscription or refund webhooks fetch the current subscription and its latest paid invoice. The captured payment must match that invoice’s ID, amount, and currency, and the subscription must use the configured Plan. Access never extends beyond the verified invoice’s billing period or the active subscription’s current period. Full refunds of the current invoice revoke access; an old refund does not revoke a later paid period. Subscription schedules are created for 120 billing cycles. Cancellation schedules the end of renewal; entitlement expires at the verified paid-through date. Handle disputes in the merchant dashboard and apply an account override when necessary.

For both gateways, verified webhooks are deduplicated. Delayed events fetch current provider state, and older reconciliation snapshots cannot overwrite newer ones. Signature failures return errors; provider failures return retriable errors without secrets. Keep webhook retry delivery enabled. Existing mandates or pending checkouts block another checkout to reduce duplicate payments. Customers can resume or cancel a pending checkout. An ambiguous failed creation retains pending state: an administrator must reconcile it with the provider before removing it. Do not switch Price/Plan IDs with active subscriptions without migrating those subscriptions.

## Gemini Live and OpenAI Realtime calls

The existing chat call button opens the new **ANSWERAI Live** panel. Choose a provider, then Start call. The previous speech-transcribe-chat-synthesize path and delegating bridge are superseded in this panel. Voice replies now come directly from the chosen realtime provider. Calls do not execute workspace tools or access the current chat's previous messages; their instructions are configurable independently.

Set server credentials and restart:

```dotenv
OPENAI_REALTIME_API_KEY=your_openai_key
GEMINI_LIVE_API_KEY=your_gemini_key
```

Enable live calls and the desired providers in the admin panel. Choose models supported by your provider account: defaults are `gpt-realtime` with voice `marin`, and `gemini-2.5-flash-native-audio-preview-12-2025` with voice `Kore`. Gemini preview availability changes; select the current supported native-audio Live model when configuring production.

Browsers connect to `/api/v1/live/call`; the server connects to fixed official provider endpoints. Authentication is sent as the first WebSocket message, never in a URL. Provider keys stay on the server. Microphone PCM uses OpenAI 24 kHz or Gemini 16 kHz; output is 24 kHz. The browser resamples Gemini input. Calls support provider voice activity detection, interruption, mute/unmute, captions, and optional camera JPEG frames at approximately one frame per second. Camera input describes what the AI sees; it does not generate outgoing video. Audio/camera media is not stored by ANSWERAI. Optional captions are saved through existing chat persistence; uncheck the option before starting to keep captions within the call panel.

Call access, voice model IDs, paid minutes, maximum duration, and camera permissions are checked server-side. Each user has one database-backed call lease; crashed workers' leases expire. Minutes are charged at session readiness and each started minute, with session access rechecked every five seconds. Provider setup failures do not consume voice minutes. Retries consume the three-starts-per-minute safety limit. Disconnecting, navigating away, or closing the panel stops microphone/camera tracks and releases the lease. Live media requires HTTPS (localhost works for development) and a browser with AudioWorklet support. Reverse proxies must support WebSockets and long-running connections.

## Validation before enabling payments

Use test credentials and test plans first. Run `python -m pytest backend/tests/test_email_verification.py backend/tests/test_billing_live.py -q` and `npm run build`. Exercise real test-mode checkout, signed webhook delivery, renewal, failed payment, cancellation, and one call on each provider. Automated tests use mocked provider APIs and do not make charges or live provider calls. SMTP verification is independent of subscriptions.
