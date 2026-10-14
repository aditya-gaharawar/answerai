import { describe, expect, it } from 'vitest';
import { downsamplePCM } from './live-call';

describe('Gemini microphone PCM conversion', () => {
	it('converts a 40 ms 24 kHz signed little-endian frame into a 16 kHz frame', () => {
		const source = new ArrayBuffer(1920);
		const input = new DataView(source);
		for (let i = 0; i < 960; i++) input.setInt16(i * 2, -30000 + i * 20, true);
		const result = downsamplePCM(source);
		expect(result.byteLength).toBe(1280);
		const converted = new DataView(result);
		expect(converted.getInt16(0, true)).toBe(-30000);
		expect(converted.getInt16(2, true)).toBe(-29970);
		expect(converted.getInt16(4, true)).toBe(-29940);
		expect(converted.getInt16(1278, true)).toBe(-10830);
	});
	it('does not modify the original provider input and handles silence', () => {
		const source = new ArrayBuffer(1920);
		const converted = downsamplePCM(source);
		expect(new Uint8Array(source).every((value) => value === 0)).toBe(true);
		expect(new Uint8Array(converted).every((value) => value === 0)).toBe(true);
	});
});

// Exercise browser cancellation and reconnect boundaries without using real media.
import { afterEach, vi } from 'vitest';
import { LiveCall } from './live-call';

afterEach(() => {
	vi.unstubAllGlobals();
	vi.useRealTimers();
});

function browser(resume: () => Promise<void> = () => Promise.resolve()) {
	vi.useFakeTimers();
	const stop = vi.fn();
	const media = { getTracks: () => [{ stop }], getAudioTracks: () => [] };
	const getUserMedia = vi.fn().mockResolvedValue(media);
	const addModule = vi.fn().mockResolvedValue(undefined);
	const close = vi.fn().mockResolvedValue(undefined);
	vi.stubGlobal('navigator', { mediaDevices: { getUserMedia } });
	vi.stubGlobal(
		'AudioContext',
		class {
			sampleRate = 24000;
			audioWorklet = { addModule };
			destination = {};
			resume = resume;
			close = close;
			createMediaStreamSource() {
				return { connect: vi.fn(), disconnect: vi.fn() };
			}
		}
	);
	vi.stubGlobal(
		'AudioWorkletNode',
		class {
			port = { onmessage: null, postMessage: vi.fn(), close: vi.fn() };
			connect = vi.fn();
			disconnect = vi.fn();
		}
	);
	const sockets: any[] = [];
	vi.stubGlobal(
		'WebSocket',
		class {
			static OPEN = 1;
			readyState = 1;
			send = vi.fn();
			close = vi.fn();
			constructor() {
				sockets.push(this);
			}
		}
	);
	vi.stubGlobal('location', { href: 'https://answerai.in/' });
	vi.stubGlobal('localStorage', { token: 'local-test-token' });
	return { stop, media, getUserMedia, addModule, close, sockets };
}

describe('Live call lifecycle', () => {
	it('does not request microphone access after cancellation during audio resume', async () => {
		let release!: () => void;
		const mocks = browser(
			() =>
				new Promise<void>((resolve) => {
					release = resolve;
				})
		);
		const call = new LiveCall(vi.fn(), vi.fn());
		const pending = call.connect('gemini');
		call.end();
		release();
		await pending;
		expect(mocks.getUserMedia).not.toHaveBeenCalled();
		expect(mocks.close).toHaveBeenCalledOnce();
		expect(call.connecting).toBe(false);
	});

	it('stops a microphone stream granted after the call has ended', async () => {
		const mocks = browser();
		let release!: (stream: unknown) => void;
		mocks.getUserMedia.mockImplementation(
			() =>
				new Promise((resolve) => {
					release = resolve;
				})
		);
		const call = new LiveCall(vi.fn(), vi.fn());
		const pending = call.connect('openai');
		await Promise.resolve();
		call.end();
		release(mocks.media);
		await pending;
		expect(mocks.stop).toHaveBeenCalledOnce();
		expect(mocks.addModule).not.toHaveBeenCalled();
	});

	it('ignores queued errors from an old socket after reconnecting', async () => {
		const mocks = browser();
		const call = new LiveCall(vi.fn(), vi.fn());
		await call.connect('openai');
		const staleError = mocks.sockets[0].onerror;
		call.end();
		expect(mocks.sockets[0].onopen).toBeNull();
		await call.connect('gemini');
		staleError();
		expect(call.connecting).toBe(true);
		expect(call.error).toBe('');
		expect(mocks.sockets[1].close).not.toHaveBeenCalled();
		call.end();
		expect(vi.getTimerCount()).toBe(0);
	});
});
