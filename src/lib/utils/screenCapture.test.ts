// @vitest-environment happy-dom
import { afterEach, it, expect, vi } from 'vitest';
import { captureScreenFrame } from './screenCapture';
afterEach(() => vi.restoreAllMocks());
it('always stops screen sharing when video playback fails', async () => {
	const stop = vi.fn();
	const stream = { getTracks: () => [{ stop }] };
	Object.defineProperty(navigator, 'mediaDevices', {
		configurable: true,
		value: { getDisplayMedia: vi.fn(async () => stream) }
	});
	vi.spyOn(HTMLMediaElement.prototype, 'srcObject', 'set').mockImplementation(() => {});
	vi.spyOn(HTMLMediaElement.prototype, 'play').mockRejectedValue(new Error('Playback failed'));
	await expect(captureScreenFrame()).rejects.toThrow('Playback failed');
	expect(stop).toHaveBeenCalledOnce();
});
it('releases a screen granted after the requesting view has closed', async () => {
	const stop = vi.fn();
	const stream = { getTracks: () => [{ stop }] };
	Object.defineProperty(navigator, 'mediaDevices', {
		configurable: true,
		value: { getDisplayMedia: vi.fn(async () => stream) }
	});
	await expect(captureScreenFrame(() => true)).resolves.toBe(null);
	expect(stop).toHaveBeenCalledOnce();
});
