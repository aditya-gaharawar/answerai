const path = require('node:path');
const fs = require('node:fs');
const output = path.resolve(process.env.SCREENSHOT_DIR || 'docs/screenshots/agentic');
fs.mkdirSync(output, { recursive: true });
const base = process.env.APP_URL || 'http://127.0.0.1:4176';
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
	let generation;
	let submitRequested;
	const submitted = new Promise((resolve) => {
		submitRequested = resolve;
	});
	page.on('console', (msg) => {
		if (msg.type() === 'error') console.log('Console:', msg.text());
	});
	await page.addInitScript(() => {
		localStorage.token = 'test-token';
		localStorage.locale = 'en-US';
	});
	await page.route('**/api/**', async (route) => {
		const url = new URL(route.request().url());
		const p = url.pathname;
		let body = route.request().method() === 'GET' ? [] : {};
		if (p.endsWith('/profile/image')) {
			await route.fulfill({ path: path.resolve('static/favicon.png') });
			return;
		}
		if (p === '/api/chat/completions') {
			generation = route.request().postDataJSON();
			submitRequested();
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					choices: [
						{
							message: {
								role: 'assistant',
								content: 'Your request was received. This preview uses mocked provider responses.'
							},
							finish_reason: 'stop'
						}
					]
				})
			});
			return;
		}
		if (p === '/api/config')
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
					enable_web_search: true,
					enable_image_generation: true,
					enable_code_interpreter: true,
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
		else if (p.includes('/models'))
			body = {
				data: [
					{
						id: 'test-model',
						name: 'ANSWERAI Reasoning',
						info: {
							meta: { capabilities: { builtin_tools: true } },
							params: {
								model_controls: {
									effort: {
										label: 'Thinking',
										default: 'balanced',
										options: {
											quick: { label: 'Quick', params: { reasoning_effort: 'low' } },
											balanced: { label: 'Balanced', params: { reasoning_effort: 'medium' } },
											deep: { label: 'Deep', params: { reasoning_effort: 'high' } }
										}
									}
								}
							}
						}
					}
				]
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
	await page.setViewportSize({ width: 1440, height: 1000 });
	await page.goto(base);
	await page
		.getByRole('heading', { name: 'What will you create today?' })
		.waitFor({ timeout: 90000 });
	await page.locator('#chat-input').waitFor();
	await page.waitForTimeout(500);
	await page.screenshot({ path: path.join(output, '02-after-desktop.png'), fullPage: true });
	await page.getByLabel('Conversation mode', { exact: true }).selectOption('agent');
	await page.getByLabel('Thinking effort', { exact: true }).selectOption('deep');
	if ((await page.getByLabel('Thinking effort', { exact: true }).inputValue()) !== 'deep')
		throw new Error('Thinking selection did not update');
	await page
		.getByRole('button', { name: 'Create an image Give your imagination a canvas' })
		.click();
	const input = page.locator('#chat-input');
	await page.waitForFunction(() =>
		document.querySelector('#chat-input')?.textContent.includes('Create an image of')
	);
	if (generation) throw new Error('Starter submitted an unfinished draft');
	await page.screenshot({ path: path.join(output, '03-agent-thinking.png'), fullPage: true });
	await page.evaluate(() => {
		document.documentElement.classList.add('dark');
		document.documentElement.classList.remove('light');
	});
	await page.waitForTimeout(600);
	await page.screenshot({ path: path.join(output, '04-after-dark.png'), fullPage: true });
	await page.setViewportSize({ width: 390, height: 844 });
	await page.screenshot({ path: path.join(output, '05-after-mobile.png'), fullPage: true });
	const overflow = await page.evaluate(
		() => document.documentElement.scrollWidth > window.innerWidth
	);
	if (overflow) throw new Error('Mobile layout overflows viewport');
	await page.setViewportSize({ width: 1440, height: 1000 });
	await input.fill('Generate a watercolor landscape.');
	await input.press('Enter');
	await Promise.race([
		submitted,
		new Promise((_, reject) => setTimeout(() => reject(new Error('No generation request')), 15000))
	]);
	if (generation.params.agent_mode !== 'agent' || generation.params.function_calling !== 'native')
		throw new Error('Agent mode not included in request');
	if (generation.params.model_controls?.['test-model']?.effort !== 'deep')
		throw new Error('Per-chat thinking choice was lost');
	if (generation.features.image_generation !== true)
		throw new Error('Image generation not enabled in request');
	if (errors.length) throw new Error(errors.join('\n'));
	console.log(
		'PASS: desktop/mobile, thinking, agent mode, image starter, request parameters; mocked APIs/providers.'
	);
	await browser.close();
})().catch((e) => {
	console.error(e);
	process.exit(1);
});
