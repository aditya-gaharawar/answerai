// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { readDataUrl } from './readDataUrl';
afterEach(() => vi.unstubAllGlobals());
it('resolves only after the file has been read', async () => {
	expect(await readDataUrl(new Blob(['hello'], { type: 'text/plain' }))).toBe(
		'data:text/plain;base64,aGVsbG8='
	);
});
it('rejects read failures instead of leaving the upload waiting', async () => {
	vi.stubGlobal(
		'FileReader',
		class {
			error = new Error('read failed');
			onerror?: () => void;
			readAsDataURL() {
				this.onerror?.();
			}
		}
	);
	await expect(readDataUrl(new Blob())).rejects.toThrow('read failed');
});
