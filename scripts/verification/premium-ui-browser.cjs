/* eslint-disable @typescript-eslint/no-require-imports -- CommonJS loads external test dependencies through NODE_PATH. */
/* Local/staging UI verification. Requires Playwright and @axe-core/playwright
 * installed outside the application. Set NODE_PATH, AAI_TEST_BASE_URL and
 * AAI_TEST_TOKEN for a synthetic test account. No API responses are fabricated.
 */
const { chromium } = require('playwright');
const { default: AxeBuilder } = require('@axe-core/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

function luminance(hex) {
	const channels = hex
		.trim()
		.replace('#', '')
		.match(/../g)
		.map((n) => parseInt(n, 16) / 255);
	const linear = channels.map((n) => (n <= 0.04045 ? n / 12.92 : ((n + 0.055) / 1.055) ** 2.4));
	return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722;
}
function contrast(a, b) {
	const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
	return (values[0] + 0.05) / (values[1] + 0.05);
}

async function main() {
	const base = process.env.AAI_TEST_BASE_URL;
	const token = process.env.AAI_TEST_TOKEN;
	assert(base && token, 'Set AAI_TEST_BASE_URL and AAI_TEST_TOKEN for local/staging.');
	const artifacts = process.env.AAI_TEST_ARTIFACTS || '/tmp/aai-premium-ui';
	await fs.mkdir(artifacts, { recursive: true });
	const browser = await chromium.launch({
		executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
		args: ['--no-sandbox', '--disable-dev-shm-usage']
	});
	const errors = [];
	const audits = [];
	const audit = async (page, scene, selector) => {
		const result = await new AxeBuilder({ page })
			.include(selector)
			.withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
			.analyze();
		audits.push({
			scene,
			violations: result.violations.map((v) => ({
				id: v.id,
				targets: v.nodes.map((n) => n.target)
			})),
			manualReview: result.incomplete.map((v) => v.id)
		});
		assert.equal(
			result.violations.length,
			0,
			`${scene}: ${JSON.stringify(audits.at(-1).violations)}`
		);
	};
	const create = async (width, preferences = {}) => {
		const context = await browser.newContext({ viewport: { width, height: 900 }, ...preferences });
		const page = await context.newPage();
		page.on('pageerror', (error) => errors.push(error.message));
		await page.addInitScript((value) => {
			localStorage.setItem('token', value);
			localStorage.setItem('sidebar', 'true');
		}, token);
		return { context, page };
	};
	const home = async (page) => {
		await page.goto(base, { waitUntil: 'domcontentloaded' });
		await page
			.getByRole('heading', { name: 'What can I help with?', exact: true })
			.waitFor({ timeout: 90000 });
		const changelog = page.getByRole('dialog', { name: "What's New in ANSWERAI" });
		if (await changelog.isVisible())
			await changelog.getByRole('button', { name: 'Close', exact: true }).click();
		await page.evaluate(() => document.fonts.ready);
	};
	const screenshot = (page, name) =>
		page.screenshot({ path: path.join(artifacts, name), animations: 'disabled' });
	try {
		for (const width of [360, 768, 1024, 1440]) {
			const { context, page } = await create(width);
			await home(page);
			assert.equal(
				await page.evaluate(() => document.documentElement.classList.contains('dark')),
				true
			);
			assert.equal(
				await page.evaluate(() => getComputedStyle(document.body).backgroundColor),
				'rgb(10, 10, 11)'
			);
			assert.equal(
				await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
				false
			);
			assert((await page.locator('.aai-home').boundingBox()).width <= 721);
			assert.equal(
				await page
					.locator('.aai-composer')
					.evaluate((node) => getComputedStyle(node).backdropFilter),
				'none'
			);
			assert(
				(await page.evaluate(() => getComputedStyle(document.body).fontFamily)).startsWith('Inter')
			);
			const palette = await page.evaluate(() => {
				const style = getComputedStyle(document.documentElement);
				return Object.fromEntries(
					[
						'bg',
						'elevated',
						'text',
						'secondary',
						'accent',
						'accent-ink',
						'success',
						'warning',
						'error'
					].map((key) => [key, style.getPropertyValue(`--aai-${key}`).trim()])
				);
			});
			for (const color of ['text', 'secondary', 'success', 'warning', 'error']) {
				assert(
					contrast(palette[color], palette.elevated) >= 4.5,
					`${color} fails AA on elevated surface`
				);
			}
			assert(
				contrast(palette['accent-ink'], palette.accent) >= 4.5,
				'Primary action contrast fails AA'
			);
			await screenshot(page, `chat-${width}.png`);
			if (width === 360 || width === 1440) await audit(page, `home-${width}`, '.aai-app');
			if (width < 768) {
				await page.locator('#sidebar-toggle-button').click();
				await page.getByRole('navigation', { name: 'Chat history', exact: true }).waitFor();
				await screenshot(page, 'drawer-360.png');
				await audit(page, 'mobile-drawer', '[role="navigation"][aria-label="Chat history"]');
				await page.getByRole('button', { name: 'Close Sidebar', exact: true }).click();
				await page
					.getByRole('navigation', { name: 'Chat history', exact: true })
					.waitFor({ state: 'hidden' });
			}
			await page.locator('#input-menu-button').click();
			await page.getByLabel('Execution mode', { exact: true }).waitFor();
			const menu = page.getByRole('menu').first();
			const box = await menu.boundingBox();
			assert(
				box.x >= 0 && box.x + box.width <= width + 1 && box.y >= 0 && box.y + box.height <= 901
			);
			await screenshot(page, `options-${width}.png`);
			if (width === 360 || width === 1440) await audit(page, `options-${width}`, '[role="menu"]');
			await page.getByLabel('Execution mode', { exact: true }).focus();
			await page.keyboard.press('Enter');
			await page.getByRole('menuitemradio', { name: 'Chat', exact: true }).waitFor();
			await page.waitForFunction(
				() => document.activeElement?.getAttribute('role') === 'menuitemradio'
			);
			await page.keyboard.press('ArrowDown');
			assert.equal(
				await page
					.getByRole('menuitemradio', { name: 'Agent', exact: true })
					.evaluate((node) => node === document.activeElement),
				true
			);
			await page.keyboard.press('Enter');
			await menu.waitFor({ state: 'detached' });
			await page.keyboard.press('Control+k');
			const dialog = page.getByRole('dialog', { name: 'Search workspace' });
			await dialog.waitFor();
			const input = dialog.locator('input').first();
			await page.waitForFunction(() => document.activeElement?.getAttribute('role') === 'combobox');
			assert.equal(await input.evaluate((node) => node === document.activeElement), true);
			await page.keyboard.press('Tab');
			assert.equal(await dialog.evaluate((node) => node.contains(document.activeElement)), true);
			await input.focus();
			await screenshot(page, `search-${width}.png`);
			if (width === 1440) await audit(page, 'keyboard-search', '[role="dialog"]');
			await page.keyboard.press('Escape');
			await dialog.waitFor({ state: 'detached' });
			if (width === 1440) {
				await page.keyboard.press('Control+.');
				const settings = page.getByRole('dialog', { name: 'Settings', exact: true });
				await settings.waitFor();
				const theme = settings.getByRole('combobox', { name: 'Theme', exact: true });
				await theme.selectOption('oled-dark');
				assert.equal(
					await page.evaluate(() => getComputedStyle(document.body).backgroundColor),
					'rgb(0, 0, 0)'
				);
				await theme.selectOption('light');
				assert.equal(
					await page.evaluate(() => document.documentElement.classList.contains('light')),
					true
				);
				await theme.selectOption('dark');
				assert.equal(
					await page.evaluate(() => getComputedStyle(document.body).backgroundColor),
					'rgb(10, 10, 11)'
				);
				await screenshot(page, 'settings-1440.png');
			}
			await context.close();
		}
		const { context, page } = await create(360, { reducedMotion: 'reduce' });
		await home(page);
		assert(
			parseFloat(
				await page.locator('.aai-home').evaluate((node) => getComputedStyle(node).animationDuration)
			) < 0.01
		);
		await page.addInitScript(() => localStorage.setItem('theme', 'light'));
		await home(page);
		assert.equal(
			await page.evaluate(() => document.documentElement.classList.contains('light')),
			true
		);
		await screenshot(page, 'light-preference-360.png');
		await page.addInitScript(() => localStorage.setItem('theme', 'dark'));
		let release;
		const gate = new Promise((resolve) => {
			release = resolve;
		});
		await page.route('**/api/v1/agent-runs/**', async (route) => {
			await gate;
			await route.continue();
		});
		const navigation = page.goto(`${base}/agents`, { waitUntil: 'domcontentloaded' });
		await page.getByRole('status', { name: 'Loading tasks' }).waitFor();
		await screenshot(page, 'tasks-loading-360.png');
		release();
		await navigation;
		await page.getByRole('status', { name: 'Loading tasks' }).waitFor({ state: 'detached' });
		await page.unroute('**/api/v1/agent-runs/**');
		await screenshot(page, 'tasks-360.png');
		await audit(page, 'tasks', '.aai-app');
		await page.route('**/api/v1/agent-runs/**', (route) => route.abort('failed'));
		await page.reload({ waitUntil: 'domcontentloaded' });
		await page.getByRole('alert').waitFor();
		assert.equal(await page.getByText('Your tasks will appear here.', { exact: true }).count(), 0);
		await screenshot(page, 'tasks-error-360.png');
		await context.close();
		assert.deepEqual(errors, []);
		await fs.writeFile(path.join(artifacts, 'accessibility.json'), JSON.stringify(audits, null, 2));
		console.log(
			JSON.stringify({
				status: 'passed',
				widths: [360, 768, 1024, 1440],
				defaultDark: true,
				preservedLightPreference: true,
				paletteContrast: true,
				keyboardMode: true,
				commandPalette: true,
				mobileDrawer: true,
				reducedMotion: true,
				loadingAndErrorStates: true,
				automatedAxeViolations: 0,
				manualReview: [...new Set(audits.flatMap((audit) => audit.manualReview))],
				pageErrors: errors
			})
		);
	} finally {
		await browser.close();
	}
}
main().catch((error) => {
	console.error(error.stack || error.message);
	process.exitCode = 1;
});
