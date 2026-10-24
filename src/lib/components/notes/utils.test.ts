// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { downloadPdf } from './utils';
vi.mock('jspdf', () => ({ default: class {} }));
vi.mock('html2canvas-pro', () => ({
	default: vi.fn(async () => {
		throw new Error('Rendering failed');
	})
}));
afterEach(() => vi.restoreAllMocks());
it('removes the temporary note DOM when PDF rendering fails', async () => {
	vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue(
		new DOMRect(0, 0, 800, 500)
	);
	const originalChildren = document.body.childElementCount;
	await expect(
		downloadPdf({
			title: 'Private note',
			data: { content: { html: '<p>Private content</p>', md: '', json: null } }
		})
	).rejects.toThrow('Rendering failed');
	expect(document.body.childElementCount).toBe(originalChildren);
	expect(document.body.textContent).not.toContain('Private content');
});
