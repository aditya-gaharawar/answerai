# ANSWERAI (AAI)

ANSWERAI is an AI chat application with local and remote model connections, retrieval, tools, and administration.

Website: https://answerai.in

## Run from source

Use Node.js 22 (with npm) and Python 3.11 or 3.12. Run everything with one command:

```sh
./run-answerai.sh
```

The script creates `.venv`, installs the full backend and frontend dependencies, builds the frontend, and serves both at http://localhost:8080. Allow several GB of free memory and disk space for the initial setup. Stop with Ctrl+C. Later, use `./run-answerai.sh --skip-setup` to start without reinstalling or rebuilding; run the default command after updating the code or dependencies.

Optionally copy `.env.example` to `.env` and edit your SMTP and model provider settings before running. Exported environment variables override `.env`; for example, `PORT=3000 ./run-answerai.sh --skip-setup`. SMTP credentials and a configured AI provider are required for email delivery and model responses respectively.

Manual setup:

```sh
npm ci
npm run build
python -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
bash start.sh
```

## Docker

```sh
docker compose up --build -d
```

The local application listens on http://localhost:3000. Compose builds the `answerai` image from this checkout; no published ANSWERAI image is required.

Set `WEBUI_URL=https://answerai.in`, configure model providers, and set a persistent `WEBUI_SECRET_KEY` for deployment. HTTPS, DNS, and services linked under answerai.in must be provisioned separately.

## Branding and verification

The Python package and CLI are `answerai`; the full application name is ANSWERAI and the PWA short name is AAI. Icons, splash assets, translations, metadata, integration headers, storage prefixes, documentation, and deployment configuration use this identity.

```sh
python scripts/audit-branding.py
python -m compileall -q backend/answerai
npm run build
```

This fork changes Python imports, Docker service and volume names, collection prefixes, and default forwarded headers. Existing deployments must migrate those names and data deliberately. Environment variables such as `WEBUI_NAME` remain configuration interfaces.

## Email verification

Enable signup email verification in **Admin → Settings → Authentication** after configuring and testing SMTP. See [email verification setup](docs/EMAIL_VERIFICATION.md) for delivery settings, the signup flow, and tests.

## Plans, payments, and live calls

The current call feature supports Gemini Live and OpenAI Realtime, with microphone audio, live captions, and optional camera input. Configure providers in **Settings → Admin → Plans, payments & live calls**.

The same settings configure Free/Plus model access, feature permissions, usage limits, account overrides, and Stripe/Razorpay subscriptions. Payment gateways and plan enforcement start disabled. See [setup and behavior](docs/PLANS_PAYMENTS_LIVE.md) for credentials, webhook endpoints, pricing, and production checks.

## License and attribution

Derived from Open WebUI, created by Timothy Jaeryang Baek. The upstream copyright, contributor agreement, license history, and license notices are retained. See [LICENSE](LICENSE), [LICENSE_HISTORY](LICENSE_HISTORY), and [LICENSE_NOTICE](LICENSE_NOTICE).

The current upstream license permits branding changes for deployments with at most 50 end users in a rolling 30-day period, specific prior written permission, or an enterprise license expressly permitting the change. This fork does not grant an exemption.
