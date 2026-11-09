/* eslint-disable @typescript-eslint/no-require-imports -- Browser dependencies are provided through NODE_PATH. */
/* Local-only rendering check. Persists clearly labelled test data through the real API,
 * checks the conversation UI, and deletes the test chat afterward. No APIs are mocked.
 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { randomUUID } = require('node:crypto');

async function main() {
	const base = process.env.AAI_TEST_BASE_URL;
	const token = process.env.AAI_TEST_TOKEN;
	assert(base && token, 'Set AAI_TEST_BASE_URL and AAI_TEST_TOKEN.');
	assert(['localhost', '127.0.0.1'].includes(new URL(base).hostname), 'Use a local test instance.');
	const artifacts = process.env.AAI_TEST_ARTIFACTS || '/tmp/aai-chat-content';
	await fs.mkdir(artifacts, { recursive: true });
	const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
	const userId = randomUUID();
	const assistantId = randomUUID();
	const timestamp = Math.floor(Date.now() / 1000);
	const model = process.env.AAI_TEST_MODEL || 'agent-validation';
	const messages = [
		{
			id: userId,
			role: 'user',
			parentId: null,
			childrenIds: [assistantId],
			models: [model],
			timestamp,
			content: 'Help me turn a product idea into a practical release plan.'
		},
		{
			id: assistantId,
			role: 'assistant',
			parentId: userId,
			childrenIds: [],
			model,
			timestamp,
			done: true,
			content: [
				'*Interface review fixture — sample content for layout verification.*',
				'',
				'Here’s a focused plan for your next release.',
				'',
				'### Start with the essentials',
				'1. Define the one problem your first release will solve.',
				'2. Build the smallest useful flow, from the first action to a clear result.',
				'3. Test it with real people before expanding the scope.',
				'',
				'### Keep the implementation small',
				'```typescript',
				'const release = {',
				'  goal: "Make the first useful action feel effortless",',
				'  checks: ["accessibility", "mobile", "recovery"],',
				'};',
				'```',
				'',
				'### Review before shipping',
				'| Area | What to verify |',
				'| --- | --- |',
				'| Experience | The main action is clear at every step. |',
				'| Reliability | Loading, errors, and retries have useful states. |',
				'| Mobile | Reading and input work comfortably on a small screen. |',
				'',
				'**Next step:** choose the first user journey and sketch the happy path.'
			].join('\n')
		}
	];
	const created = await fetch(`${base}/api/v1/chats/new`, {
		method: 'POST',
		headers,
		body: JSON.stringify({
			chat: {
				title: 'Interface review fixture',
				models: [model],
				history: {
					messages: Object.fromEntries(messages.map((m) => [m.id, m])),
					currentId: assistantId
				},
				messages,
				timestamp
			}
		})
	});
	assert(created.ok, `Could not create test chat: HTTP ${created.status}`);
	const chat = await created.json();
	const browser = await chromium.launch({
		executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
		args: ['--no-sandbox', '--disable-dev-shm-usage']
	});
	const errors = [];
	try {
		for (const width of [360, 768, 1440]) {
			const context = await browser.newContext({ viewport: { width, height: 900 } });
			const page = await context.newPage();
			page.on('pageerror', (error) => errors.push(error.message));
			await page.addInitScript((value) => {
				localStorage.setItem('token', value);
				localStorage.setItem('sidebar', 'true');
			}, token);
			await page.goto(`${base}/c/${chat.id}`, { waitUntil: 'domcontentloaded' });
			await page.locator('.aai-code-block').waitFor({ timeout: 90000 });
			await page.locator('.aai-message table').waitFor();
			await page.evaluate(() => document.fonts.ready);
			await page.locator('#messages-container').evaluate((node) => {
				node.scrollTop = 0;
			});
			assert.equal(
				await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
				false
			);
			const composer = await page.locator('.aai-composer').boundingBox();
			assert(
				composer.y + composer.height <= 901 && composer.y > 600,
				'Conversation input is not anchored'
			);
			assert.equal(
				await page
					.locator('.aai-code-block')
					.getByRole('button', { name: 'Copy', exact: true })
					.count(),
				1
			);
			await page.screenshot({
				path: path.join(artifacts, `conversation-${width}.png`),
				animations: 'disabled'
			});
			await context.close();
		}
		assert.deepEqual(errors, []);
		console.log(
			JSON.stringify({
				status: 'passed',
				widths: [360, 768, 1440],
				code: true,
				table: true,
				anchoredInput: true,
				pageErrors: errors
			})
		);
	} finally {
		await browser.close();
		const deleted = await fetch(`${base}/api/v1/chats/${chat.id}`, { method: 'DELETE', headers });
		assert(deleted.ok, `Could not delete test chat: HTTP ${deleted.status}`);
	}
}
main().catch((error) => {
	console.error(error.stack || error.message);
	process.exitCode = 1;
});
