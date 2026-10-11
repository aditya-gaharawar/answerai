# ANSWERAI email verification

New password signups can be required to confirm their email before receiving a session, API access, or an MFA challenge. Administrator approval remains a separate requirement. Existing accounts, administrator-created accounts, and new accounts provisioned through an identity provider retain their existing behavior. An existing unverified password account cannot bypass verification by signing in through OAuth or a trusted-header provider.

## Configure delivery

1. Keep a stable `WEBUI_SECRET_KEY` across application instances and restarts.
2. In **Admin → Settings → Authentication → Email verification**, enter your SMTP host, port, username, password, sender address, and public application URL.
3. Use STARTTLS on port 587, or TLS on port 465. Certificate validation is always enabled. Ensure the configured sender is approved by your mail provider.
4. Select **Save and send test email**. The test goes to the signed-in administrator's address.
5. Enable **Require email verification for new signups** and save Authentication settings. Verification is disabled by default.

The public URL must be the URL users can reach, such as `https://answerai.in`. HTTP is supported only for localhost development. SMTP authentication is optional for a trusted mail relay that permits unauthenticated delivery; encrypted transport is still required.

SMTP passwords entered through the admin interface are encrypted with a key derived from `WEBUI_SECRET_KEY`. The API returns only whether a password is configured. A blank password keeps the current credential; the explicit clear option removes it, including an environment-provided fallback. After rotating the application secret, re-enter the SMTP password. Other settings persist through the existing configuration system.

Environment variables can configure delivery instead:

```dotenv
ENABLE_EMAIL_VERIFICATION=true
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_SECURITY=starttls
SMTP_USERNAME=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@answerai.in
SMTP_FROM_NAME=ANSWERAI
WEBUI_URL=https://answerai.in
EMAIL_VERIFICATION_TOKEN_TTL_SECONDS=3600
EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS=60
```

Do not commit a real password. As with other application settings, saved database configuration takes precedence over environment defaults when persistent configuration is enabled.

## User flow

After signup, ANSWERAI displays a check-your-email screen instead of signing the user in. The email contains plain-text and HTML versions of a link. Opening it displays a confirmation page; the user presses **Verify email**, then signs in normally. An email scanner following the link cannot consume the token through a GET request.

Tokens contain 256 bits of randomness; only their SHA-256 hashes are stored. Links expire after one hour by default, work once, and verify only the credential email recorded when the link was created. The token is carried in a URL fragment and removed from browser history when the page loads. It is never a login token.

Users can resend from the signup/sign-in screen or request a replacement from an invalid/expired-link screen. Only the newest link works. A database-backed cooldown limits concurrent sends across application workers. Address limits allow five resend requests per hour; IP limits allow ten resend requests and thirty verification attempts per fifteen minutes. Redis shares these request limits across workers; the existing in-memory fallback applies per worker. Signup is also limited to ten attempts per IP per fifteen minutes.

Resend responses do not disclose whether an account exists, is already verified, or encountered a mail failure. Delivery runs after the response. SMTP failures leave the account unverified, invalidate the failed token, and permit a later resend after the cooldown. Application logs report delivery failure without including credentials or tokens. Administrative mail tests report delivery errors to the administrator.

Disabling verification changes future signup requirements. Accounts already awaiting verification still must verify, and their valid links and resend flow continue working.

## Database and validation

Normal startup applies Alembic revision `e8a14c7b9206`. It adds `auth.email_verified` with existing rows set to true and a separate token table. Deployments that disable automatic migrations must apply the migration before starting the updated application. Back up application data before a production upgrade.

```sh
python -m pip install -r backend/tests/requirements.txt
python -m pytest backend/tests/test_email_verification.py -q
python scripts/audit-branding.py
npm run test:frontend -- --run
NODE_OPTIONS=--max-old-space-size=8192 npm run build
```

Automated tests use isolated SQLite databases and mocked SMTP, including token replay, expiry, replacement, concurrent consumption, delivery failure, configuration encryption, administrator-only endpoints, migration rollback, and MFA ordering. Live delivery requires configured SMTP credentials and network access to that provider.
