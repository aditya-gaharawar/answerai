import { describe, expect, it } from 'vitest';
import { buildIframeSandbox } from './iframe-sandbox';

describe('untrusted HTML sandbox policy', () => {
	it('keeps the strict empty sandbox instead of removing the attribute', () => {
		expect(buildIframeSandbox({})).toBe('');
		expect(
			buildIframeSandbox({
				allowScripts: false,
				allowForms: false,
				allowSameOrigin: false,
				allowPopups: false,
				allowDownloads: false
			})
		).toBe('');
	});
	it('never combines executable scripts with access to the application origin', () => {
		expect(buildIframeSandbox({ allowScripts: true, allowSameOrigin: true }).split(' ')).toEqual([
			'allow-scripts'
		]);
	});
	it('allows static same-origin content and preserves explicit safe capabilities', () => {
		expect(
			buildIframeSandbox({ allowScripts: false, allowSameOrigin: true, allowDownloads: true })
		).toBe('allow-same-origin allow-downloads');
		expect(buildIframeSandbox({ allowScripts: true, allowForms: true, allowPopups: true })).toBe(
			'allow-scripts allow-forms allow-popups'
		);
	});
});
