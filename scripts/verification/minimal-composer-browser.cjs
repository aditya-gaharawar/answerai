/* Local/staging only: creates a real test conversation. Uses an explicitly configured
 * test account/provider; no requests are mocked or intercepted in this browser test.
 * Install Playwright outside the repository and set NODE_PATH if necessary.
 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

async function main() {
	const base = process.env.AAI_TEST_BASE_URL;
	const token = process.env.AAI_TEST_TOKEN;
	const model = process.env.AAI_TEST_MODEL;
	const artifacts = process.env.AAI_TEST_ARTIFACTS || '/tmp/aai-composer-verification';
	if (!base || !token || !model)
		throw new Error(
			'Set AAI_TEST_BASE_URL, AAI_TEST_TOKEN and AAI_TEST_MODEL for a test environment.'
		);
	await fs.mkdir(artifacts, { recursive: true });
	const browser = await chromium.launch({
		executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
		headless: true,
		args: ['--no-sandbox', '--disable-dev-shm-usage']
	});
	try {
		const page = await browser.newPage();
		const errors = [];
		page.on('pageerror', (error) => errors.push(error.message));
		await page.addInitScript((value) => localStorage.setItem('token', value), token);
		const openMenu = async () => {
			await page.locator('#input-menu-button').click();
			await page.getByLabel('Execution mode', { exact: true }).waitFor({ state: 'visible' });
		};
		const dismiss = async () => {
			await page.keyboard.press('Escape');
			await page.getByRole('menu').first().waitFor({ state: 'detached' });
		};
		for (const width of [320, 390, 768, 1440]) {
			await page.setViewportSize({ width, height: 844 });
			await page.goto(base, { waitUntil: 'domcontentloaded' });
			await page.getByRole('heading', { name: 'What can I help with?', exact: true }).waitFor();
			const composer = page.locator('form').filter({ has: page.locator('#chat-input') });
			assert.equal(
				await composer.getByRole('button').count(),
				2,
				'Composer has extra visible controls'
			);
			assert.equal(await composer.getByRole('button', { name: 'More', exact: true }).count(), 1);
			assert.equal(
				await composer.getByRole('button', { name: 'Send message', exact: true }).count(),
				1
			);
			assert.equal(await page.getByLabel('Execution mode').count(), 0);
			assert.equal(await page.locator('#model-selector-model-button').count(), 0);
			assert.equal(
				await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
				false
			);
			await page.screenshot({
				path: path.join(artifacts, `chat-${width}.png`),
				animations: 'disabled'
			});
			await openMenu();
			const box = await page.getByRole('menu').first().boundingBox();
			assert(box && box.x >= 0 && box.x + box.width <= width + 1, 'Menu overflows screen width');
			assert(box.y >= 0 && box.y + box.height <= 845, 'Menu overflows screen height');
			await page.screenshot({
				path: path.join(artifacts, `menu-${width}.png`),
				animations: 'disabled'
			});
			await page.getByLabel('Execution mode').selectOption('agent');
			await page.getByLabel('Execution mode').waitFor({ state: 'detached' });
			await openMenu();
			assert.equal(await page.getByLabel('Execution mode').inputValue(), 'agent');
			await page.getByLabel('Execution mode').selectOption('auto');
			await openMenu();
			await page.getByRole('menuitem', { name: 'Add attachments', exact: true }).click();
			await page.getByRole('menuitem', { name: 'Upload Files', exact: true }).waitFor();
			await dismiss();
			await openMenu();
			await page.getByRole('menuitem', { name: 'Add attachments', exact: true }).click();
			await page.getByRole('menuitem', { name: 'Attachments', exact: true }).click();
			await page.getByLabel('Execution mode').waitFor();
			await dismiss();
		}
		await page.setViewportSize({ width: 390, height: 844 });
		await openMenu();
		await page.locator('#model-selector-model-button').click();
		await page.getByRole('listbox', { name: 'Available models' }).waitFor();
		await page.getByRole('option').filter({ hasText: model }).first().click();
		await page.getByRole('listbox', { name: 'Available models' }).waitFor({ state: 'detached' });
		await page.getByLabel('Model controls', { exact: true }).click();
		assert.equal(await page.getByRole('menu').count(), 2, 'Nested model controls did not open');
		await dismiss();
		await openMenu();
		await page.locator('#integration-menu-button').click();
		assert.equal(await page.getByRole('menu').count(), 2, 'Nested integrations did not open');
		await dismiss();
		await page.evaluate(() => document.documentElement.classList.add('dark'));
		await page.screenshot({
			path: path.join(artifacts, 'chat-mobile-dark.png'),
			animations: 'disabled'
		});
		await openMenu();
		await page.screenshot({
			path: path.join(artifacts, 'menu-mobile-dark.png'),
			animations: 'disabled'
		});
		await page.setViewportSize({ width: 390, height: 420 });
		await page.screenshot({
			path: path.join(artifacts, 'menu-short-viewport.png'),
			animations: 'disabled'
		});
		const shortBox = await page.getByRole('menu').first().boundingBox();
		assert(shortBox && shortBox.y >= 0 && shortBox.y + shortBox.height <= 421);
		await dismiss();
		await page.setViewportSize({ width: 390, height: 844 });
		await page.evaluate(() => document.documentElement.classList.remove('dark'));
		await openMenu();
		const [chooser] = await Promise.all([
			page.waitForEvent('filechooser'),
			(async () => {
				await page.getByRole('menuitem', { name: 'Add attachments', exact: true }).click();
				await page.getByRole('menuitem', { name: 'Upload Files', exact: true }).click();
			})()
		]);
		await chooser.setFiles([]);
		await page.locator('#chat-input').fill('Say hello briefly.');
		const [response] = await Promise.all([
			page.waitForResponse(
				(response) =>
					response.url().includes('/chat/completions') && response.request().method() === 'POST'
			),
			page.getByRole('button', { name: 'Send message', exact: true }).click()
		]);
		assert(response.ok(), `Chat submission failed: HTTP ${response.status()}`);
		await page.locator('#response-content-container').filter({ hasText: /\S/ }).first().waitFor();
		await openMenu();
		await page.getByRole('menuitem', { name: 'Background tasks' }).click();
		await page.getByRole('heading', { name: 'Agent tasks', exact: true }).waitFor();
		assert.deepEqual(errors, []);
		console.log(
			JSON.stringify({
				status: 'passed',
				widths: [320, 390, 768, 1440],
				compactComposer: true,
				modeSelection: true,
				nestedModels: true,
				nestedControls: true,
				nestedIntegrations: true,
				attachments: true,
				shortViewport: true,
				chatSubmission: true,
				backgroundTaskNavigation: true,
				pageErrors: errors
			})
		);
	} finally {
		await browser.close();
	}
}
main().catch((error) => {
	console.error(error.message);
	process.exitCode = 1;
});
