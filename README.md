# ANSWERAI (AAI)

ANSWERAI is an AI chat application with local and remote model connections, retrieval, tools, and administration.

Website: https://answerai.in

## Run from source

Use Node.js 22 and Python 3.11 or later. The production frontend build needs several GB of memory; set `NODE_OPTIONS=--max-old-space-size=8192` when Node reaches its default heap limit.

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

## License and attribution

Derived from Open WebUI, created by Timothy Jaeryang Baek. The upstream copyright, contributor agreement, license history, and license notices are retained. See [LICENSE](LICENSE), [LICENSE_HISTORY](LICENSE_HISTORY), and [LICENSE_NOTICE](LICENSE_NOTICE).

The current upstream license permits branding changes for deployments with at most 50 end users in a rolling 30-day period, specific prior written permission, or an enterprise license expressly permitting the change. This fork does not grant an exemption.
