/* Local/staging smoke test. Requires an explicitly configured test model and account.
 * Install Playwright outside the repo and expose it through NODE_PATH if necessary.
 * Never point this at production: it creates a real conversation and execution.
 */
const { chromium } = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');

async function main() {
	const base = process.env.AAI_TEST_BASE_URL;
	const token = process.env.AAI_TEST_TOKEN;
	const model = process.env.AAI_TEST_MODEL;
	const artifacts = process.env.AAI_TEST_ARTIFACTS || '/tmp/aai-agentic-verification';
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
		const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
		const errors = [];
		page.on('pageerror', (error) => errors.push(error.message));
		await page.addInitScript((value) => localStorage.setItem('token', value), token);
		await page.goto(`${base}/agents`, { waitUntil: 'domcontentloaded', timeout: 120000 });
		await page.getByRole('heading', { name: 'Agent tasks' }).waitFor({ timeout: 60000 });
		const changelog = page.getByRole('dialog', { name: "What's New in ANSWERAI" });
		if (await changelog.isVisible())
			await changelog.getByRole('button', { name: 'Close', exact: true }).click();
		await page.getByLabel('Model', { exact: true }).selectOption(model);
		await page.getByText('Options', { exact: true }).click();
		await page.getByLabel('Web research', { exact: true }).uncheck();
		await page
			.getByLabel('Objective', { exact: true })
			.fill('Get the current timestamp using the available tool, then summarize the result.');
		const [response] = await Promise.all([
			page.waitForResponse(
				(response) =>
					new URL(response.url()).pathname === '/api/v1/agent-runs/' &&
					response.request().method() === 'POST'
			),
			page.getByRole('button', { name: 'Start task' }).click()
		]);
		if (!response.ok()) throw new Error(`Task creation failed: HTTP ${response.status()}`);
		const run = await response.json();
		let article = page
			.locator('article')
			.filter({ has: page.locator(`a[href="/c/${run.chat_id}"]`) });
		await article.getByText('needs review', { exact: true }).waitFor({ timeout: 90000 });
		await page.reload({ waitUntil: 'domcontentloaded' });
		article = page.locator('article').filter({ has: page.locator(`a[href="/c/${run.chat_id}"]`) });
		await article.getByText('needs review', { exact: true }).waitFor();
		await article.locator('summary').click();
		if (!(await article.innerText()).includes('get_current_timestamp'))
			throw new Error('Timestamp execution missing from persisted activity.');
		await page.screenshot({ path: path.join(artifacts, 'agent-desktop.png'), fullPage: true });
		await article.getByRole('button', { name: 'I verified the result' }).click();
		await article.getByText('completed', { exact: true }).waitFor();
		await page.setViewportSize({ width: 390, height: 844 });
		await page.screenshot({ path: path.join(artifacts, 'agent-mobile.png'), fullPage: true });
		if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth))
			throw new Error('Mobile page overflows viewport.');
		await page.goto(base, { waitUntil: 'domcontentloaded' });
		await page.locator('#input-menu-button').click();
		const mode = page.getByLabel('Execution mode', { exact: true });
		await mode.waitFor({ state: 'visible' });
		await mode.click();
		await page.getByRole('menuitemradio', { name: 'Agent', exact: true }).click();
		await mode.waitFor({ state: 'detached' });
		await page.locator('#input-menu-button').click();
		await mode.click();
		if (
			(await page
				.getByRole('menuitemradio', { name: 'Agent', exact: true })
				.getAttribute('aria-checked')) !== 'true'
		)
			throw new Error('Agent mode was not selected.');
		await page.getByRole('menuitemradio', { name: 'Agent', exact: true }).click();
		await mode.waitFor({ state: 'detached' });
		await page.locator('#input-menu-button').click();
		await page.getByRole('menuitem', { name: 'Background tasks' }).click();
		await page.getByRole('heading', { name: 'Agent tasks', exact: true }).waitFor();
		if (errors.length) throw new Error(`Browser raised ${errors.length} uncaught errors.`);
		console.log(
			JSON.stringify({
				status: 'passed',
				refreshPersistence: true,
				toolEvent: true,
				verification: true,
				mobileLayout: true,
				modeSelection: true,
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
