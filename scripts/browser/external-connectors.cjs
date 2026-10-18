const path = require('node:path');
const catalog = require('../../backend/answerai/connectors/catalog.json');
const output = path.resolve('docs/screenshots/connectors');
require('node:fs').mkdirSync(output, { recursive: true });
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
	const browser = await chromium.launch({
		executablePath: process.env.CHROME_BIN,
		headless: true,
		args: ['--no-sandbox', '--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream']
	});
	const context = await browser.newContext({ permissions: ['microphone', 'camera'] });
	const page = await context.newPage();
	const errors = [];
	page.on('response', (response) => {
		if (response.status() >= 400)
			console.log('HTTP resource', response.status(), new URL(response.url()).pathname);
	});
	page.on('pageerror', (e) => {
		errors.push(e.stack);
		console.log('PAGE ERROR', e.stack);
	});
	const features = {
		uploads: true,
		images: true,
		web_search: true,
		code_interpreter: true,
		tools: true,
		memory: true,
		automations: true,
		live_calls: true,
		live_video: true,
		direct_connections: false
	};
	const plan = {
		models: ['*'],
		feature_limits: Object.fromEntries(Object.keys(features).map((k) => [k, 100])),
		messages_per_day: 1000,
		requests_per_minute: 60,
		live_minutes_per_day: 60,
		max_call_minutes: 30,
		features
	};
	let ready = false;
	let saved = [];
	let stale = false;
	page.on('console', (msg) => {
		if (msg.type() === 'error') console.log('Console:', msg.text());
	});
	await page.addInitScript(() => {
		localStorage.token = 'test-token';
		localStorage.locale = 'en-US';
		window.testMediaTracks = [];
		const media = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
		navigator.mediaDevices.getUserMedia = async (options) => {
			const stream = await media(options);
			window.testMediaTracks.push(...stream.getTracks());
			return stream;
		};
	});
	await page.route('**/api/**', async (route) => {
		const url = new URL(route.request().url());
		const p = url.pathname;
		let body = route.request().method() === 'GET' ? [] : {};
		if (p === '/api/v1/configs/connectors/catalog') body = catalog;
		else if (p === '/api/v1/configs/connectors/test') {
			const data = route.request().postDataJSON();
			if (stale) {
				await new Promise((resolve) => setTimeout(resolve, 600));
			}
			body = data.key.includes('expired')
				? { status: 'unauthorized', message: 'The access token is invalid or expired.' }
				: data.connector_id === 'slack'
					? {
							status: 'forbidden',
							message: 'Check Slack token type, scopes, and workspace policy.'
						}
					: {
							status: 'connected',
							message:
								'Credentials accepted. Individual tools still require their documented scopes and resource access.'
						};
		} else if (p === '/api/v1/configs/tool_servers') {
			if (route.request().method() === 'POST')
				saved = route.request().postDataJSON().TOOL_SERVER_CONNECTIONS;
			body = { TOOL_SERVER_CONNECTIONS: saved };
		} else if (p === '/api/v1/configs/connections')
			body = {
				ENABLE_DIRECT_CONNECTIONS: false,
				ENABLE_DIRECT_INTEGRATIONS: false,
				ENABLE_BASE_MODELS_CACHE: false
			};
		else if (p === '/api/v1/configs/terminal_servers') body = { TERMINAL_SERVER_CONNECTIONS: [] };
		else if (p.endsWith('/profile/image')) {
			await route.fulfill({ path: path.resolve('static/favicon.png') });
			return;
		} else if (p === '/api/v1/notes/note-test/update') {
			body = {
				id: 'note-test',
				user_id: 'user-test',
				write_access: false,
				access_grants: [],
				title: 'Review note',
				data: route.request().postDataJSON().data,
				meta: {},
				created_at: 1,
				updated_at: 2
			};
		} else if (p === '/api/v1/notes/note-test')
			body = {
				id: 'note-test',
				user_id: 'user-test',
				write_access: false,
				access_grants: [],
				title: 'Review note',
				data: {
					content: {
						md: 'Public paragraph\n\nPrivate paragraph',
						html: '<p>Public paragraph</p><p>Private paragraph</p>',
						json: {
							type: 'doc',
							content: [
								{ type: 'paragraph', content: [{ type: 'text', text: 'Public paragraph' }] },
								{ type: 'paragraph', content: [{ type: 'text', text: 'Private paragraph' }] }
							]
						}
					}
				},
				meta: {},
				created_at: 1,
				updated_at: 1
			};
		else if (p === '/api/v1/notes/search') {
			const query = url.searchParams.get('query') ?? '';
			if (query === 'broken') {
				await route.fulfill({
					status: 500,
					contentType: 'application/json',
					body: JSON.stringify({ detail: 'Search unavailable' })
				});
				return;
			}
			if (query === 'old') await new Promise((resolve) => setTimeout(resolve, 2000));
			body = {
				items: [
					{
						id: 'list-note',
						user_id: 'user-test',
						title:
							query === 'old' ? 'Stale note' : query === 'new' ? 'Current note' : 'Visible note',
						data: null,
						access_grants: [],
						created_at: Date.now() * 1000000,
						updated_at: Date.now() * 1000000,
						user: { id: 'user-test', name: 'Test' }
					}
				],
				total: 1
			};
		} else if (p === '/api/config')
			body = {
				name: 'ANSWERAI',
				version: '0.12.1',
				default_locale: 'en-US',
				onboarding: false,
				features: {
					auth: true,
					enable_signup: true,
					enable_login_form: true,
					enable_notes: true,
					enable_tool_servers: true,
					enable_tools: true,
					enable_websocket: false,
					enable_version_update_check: false
				},
				oauth: { providers: {} },
				audio: {
					realtime: { enabled: true },
					stt: { engine: 'openai' },
					tts: { engine: 'openai' }
				},
				metadata: {},
				default_models: 'test-model'
			};
		else if (p === '/api/version') body = { version: '0.12.1' };
		else if (p === '/api/v1/auths/')
			body = {
				id: 'user-test',
				email: 'test@example.com',
				name: 'Test',
				role: 'admin',
				permissions: { chat: { call: true } },
				settings: {},
				token: 'test-token'
			};
		else if (p === '/api/v1/billing/me')
			body = {
				plan: 'free',
				enabled: true,
				entitlements: plan,
				usage: [
					{
						metric: 'messages',
						window: 86400,
						used: 3,
						resets_at: Math.floor(Date.now() / 1000) + 3600
					}
				],
				subscriptions: []
			};
		else if (p === '/api/v1/billing/plans')
			body = { enabled: true, free: { ...plan, messages_per_day: 20 }, plus: plan, prices: [] };
		else if (p === '/api/v1/live/providers')
			body = {
				enabled: true,
				providers: [
					{ id: 'openai', name: 'OpenAI Realtime', model: 'gpt-realtime', allowed: true },
					{ id: 'gemini', name: 'Gemini Live', model: 'gemini-test', allowed: true }
				],
				default_provider: 'openai',
				allowed: true,
				camera_allowed: true,
				max_call_minutes: 30
			};
		else if (p === '/api/v1/billing/config')
			body = {
				enabled: true,
				free: plan,
				plus: plan,
				feature_keys: Object.keys(features),
				credentials: {},
				public_url: 'https://answerai.in',
				stripe_enabled: false,
				razorpay_enabled: false
			};
		else if (p === '/api/v1/live/config')
			body = {
				enabled: true,
				default_provider: 'openai',
				openai_model: 'gpt-realtime',
				gemini_model: 'gemini-test'
			};
		else if (p === '/api/v1/admin/controls/policy')
			body = {
				max_request_mib: 64,
				allow_user_python_tools: false,
				allowed_cookie_origins: [],
				trusted_oauth_email_providers: []
			};
		else if (p === '/api/v1/admin/controls/overview')
			body = { active_calls: 1, active_subscriptions: 2, verified_webhook_events: 3 };
		else if (p === '/api/v1/admin/controls/actions') body = [];
		else if (p.startsWith('/api/v1/admin/controls/accounts/'))
			body = {
				id: 'member-test',
				name: 'Member',
				email: 'member@example.com',
				role: 'user',
				plan: 'free',
				login_enabled: true,
				email_verified: true,
				active_call: false,
				usage: [],
				subscriptions: []
			};
		else if (p.includes('/models'))
			body = {
				data: [{ id: 'test-model', name: 'Test model', info: { meta: { capabilities: {} } } }]
			};
		else if (
			p.includes('/chats') &&
			(p.endsWith('/') || p.includes('/pinned') || p.includes('/list'))
		)
			body = [];
		else if (p.includes('/settings'))
			body = { ui: { version: '0.12.1', showChangelog: false }, keybindings: {} };
		else if (
			[
				'/api/v1/tools/',
				'/api/v1/skills/',
				'/api/v1/functions/',
				'/api/v1/channels/',
				'/api/v1/folders/',
				'/api/v1/chats/all/tags',
				'/api/v1/prompts/',
				'/api/v1/configs/banners',
				'/api/v1/notes/pinned'
			].includes(p)
		)
			body = [];
		if (Object.keys(body).length === 0 && p !== '/api/v1/chats/config')
			console.log('Default mock:', p);
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify(body)
		});
	});

	await page.route('**/ws/**', (route) => route.abort());
	await page.setViewportSize({ width: 1440, height: 1100 });
	await page.goto(
		(process.env.APP_URL || 'http://127.0.0.1:4176') + '/?settings=admin%3Aintegrations'
	);
	await page.locator('fieldset').first().getByRole('button').first().click({ timeout: 90000 });
	const picker = page.getByLabel('Start from a connector', { exact: true });
	await picker.locator('option[value=gmail]').waitFor({ state: 'attached' });
	await picker.selectOption('gmail');
	const key = page.getByPlaceholder('API Key', { exact: true });
	const test = page.getByRole('button', { name: 'Test credentials', exact: true });
	if (!(await test.isDisabled())) throw new Error('Empty token can be tested');
	await key.fill('fixture-google-token');
	await test.click();
	await page.locator('[data-connector-status=connected]').waitFor();
	await page.screenshot({ path: path.join(output, 'gmail-setup.png'), fullPage: true });
	await key.fill('fixture-expired-token');
	if (await page.locator('[data-connector-status=connected]').count())
		throw new Error('Old credential result remained visible');
	await test.click();
	await page.locator('[data-connector-status=unauthorized]').waitFor();
	await picker.selectOption('slack');
	if ((await key.inputValue()) !== '') throw new Error('Token leaked into another connector');
	await key.fill('fixture-slack-token');
	await test.click();
	await page.locator('[data-connector-status=forbidden]').waitFor();
	await page.screenshot({ path: path.join(output, 'slack-scope-check.png'), fullPage: true });
	stale = true;
	await key.fill('fixture-google-token');
	await test.click();
	await picker.selectOption('github');
	await page.waitForTimeout(800);
	if (await page.locator('[data-connector-status]').count())
		throw new Error('Stale result shown for another provider');
	stale = false;
	await key.fill('fixture-github-token');
	await test.click();
	await page.locator('[data-connector-status=connected]').waitFor();
	await page.getByRole('dialog').last().getByRole('button', { name: 'Save', exact: true }).click();
	await page.waitForFunction(() => !document.querySelector('#connector-preset'));
	if (saved.length !== 1 || saved[0].info.connector_id !== 'github')
		throw new Error('Connector not saved');
	if (saved[0].config.access_grants.length !== 0) throw new Error('Connector unexpectedly shared');
	if (saved[0].forward_cookies !== false) throw new Error('Connector forwards application cookies');
	const spec = JSON.parse(saved[0].spec);
	if (
		Object.values(spec.paths).some((methods) =>
			Object.keys(methods).some((method) => method !== 'get')
		)
	)
		throw new Error('Write tools enabled');
	await page.locator('fieldset').first().getByRole('button').first().click();
	await picker.selectOption('notion');
	await page.getByRole('button', { name: 'Register Client', exact: true }).waitFor();
	const before = await page.locator('#enter-id').inputValue();
	await page.locator('#enter-name').fill('Notion workspace renamed');
	if ((await page.locator('#enter-id').inputValue()) !== before)
		throw new Error('OAuth connection ID changed with display name');
	await page.screenshot({ path: path.join(output, 'notion-oauth.png'), fullPage: true });
	await picker.selectOption('');
	await page.locator('#enter-name').fill('');
	await page.locator('#enter-name').pressSequentially('Custom connector');
	if ((await page.locator('#enter-id').inputValue()) !== 'custom-connector')
		throw new Error('Custom connection ID no longer follows its name');
	if (errors.length) throw new Error(errors.join('\n'));
	console.log(
		'PASS: Gmail preset, invalid-token result, Slack scope error, stale-result isolation, GitHub private read-only save, Notion OAuth; mocked providers.'
	);
	await browser.close();
})().catch((error) => {
	console.error(error);
	process.exit(1);
});
