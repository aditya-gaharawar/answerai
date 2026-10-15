import { afterEach, describe, expect, it, vi } from 'vitest';

afterEach(() => {
	vi.unstubAllGlobals();
	vi.useRealTimers();
	vi.resetModules();
});

describe('Google Drive OAuth lifecycle', () => {
	it('reuses a valid token and refreshes it before expiry', async () => {
		vi.useFakeTimers();
		vi.setSystemTime(100000);
		let requests = 0;
		vi.stubGlobal('google', {
			accounts: {
				oauth2: {
					initTokenClient: ({ callback }: { callback: (response: object) => void }) => ({
						requestAccessToken: () => {
							requests++;
							callback({ access_token: `token-${requests}`, expires_in: '120' });
						}
					})
				}
			}
		});
		const { getAuthToken } = await import('./google-drive-picker');
		expect(await getAuthToken()).toBe('token-1');
		expect(await getAuthToken()).toBe('token-1');
		vi.setSystemTime(161000);
		expect(await getAuthToken()).toBe('token-2');
		expect(requests).toBe(2);
	});
	it('loads the auth SDK when the picker has already created a google global', async () => {
		vi.stubGlobal('google', { picker: {} });
		const appendChild = vi.fn((script: { onload: () => void }) => script.onload());
		vi.stubGlobal('document', { createElement: () => ({}), body: { appendChild } });
		const { loadGoogleAuthApi } = await import('./google-drive-picker');
		await loadGoogleAuthApi();
		expect(appendChild).toHaveBeenCalledOnce();
	});
});
