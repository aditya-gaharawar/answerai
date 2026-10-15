// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { mount, unmount, tick } from 'svelte';
import { writable } from 'svelte/store';
import VoiceRecording from './VoiceRecording.svelte';
import { config } from '$lib/stores';

vi.mock('$lib/utils', () => ({
	blobToFile: vi.fn(),
	calculateSHA256: vi.fn(),
	extractCurlyBraceWords: vi.fn()
}));
vi.mock('$lib/apis/audio', () => ({ transcribeAudio: vi.fn() }));
afterEach(() => {
	vi.unstubAllGlobals();
	vi.restoreAllMocks();
	config.set(undefined);
	document.body.innerHTML = '';
});
describe('voice recorder ownership', () => {
	it('stops a microphone granted after the component unmounts', async () => {
		let grant!: (stream: MediaStream) => void;
		const request = new Promise<MediaStream>((resolve) => {
			grant = resolve;
		});
		const stop = vi.fn();
		const stream = { getTracks: () => [{ stop }] } as unknown as MediaStream;
		const getUserMedia = vi.fn(() => request);
		Object.defineProperty(navigator, 'mediaDevices', {
			configurable: true,
			value: { getUserMedia }
		});
		const recorder = vi.fn();
		vi.stubGlobal('MediaRecorder', recorder);
		const target = document.createElement('div');
		document.body.appendChild(target);
		const component = mount(VoiceRecording, {
			target,
			props: { recording: true },
			context: new Map([['i18n', writable({ t: (key: string) => key, language: 'en-US' })]])
		});
		await tick();
		expect(getUserMedia).toHaveBeenCalledOnce();
		await unmount(component);
		grant(stream);
		await request;
		await tick();
		expect(stop).toHaveBeenCalledOnce();
		expect(recorder).not.toHaveBeenCalled();
	});
});

describe('recorder initialization failures', () => {
	it('releases the acquired microphone when MediaRecorder rejects the format', async () => {
		const stop = vi.fn();
		const stream = { getTracks: () => [{ stop }] } as unknown as MediaStream;
		Object.defineProperty(navigator, 'mediaDevices', {
			configurable: true,
			value: { getUserMedia: vi.fn(async () => stream) }
		});
		class UnsupportedRecorder {
			static isTypeSupported() {
				return false;
			}
			constructor() {
				throw new Error('Unsupported recorder');
			}
		}
		vi.stubGlobal('MediaRecorder', UnsupportedRecorder);
		const target = document.createElement('div');
		document.body.appendChild(target);
		const component = mount(VoiceRecording, {
			target,
			props: { recording: true },
			context: new Map([['i18n', writable({ t: (key: string) => key, language: 'en-US' })]])
		});
		await tick();
		await tick();
		expect(stop).toHaveBeenCalled();
		await unmount(component);
	});
});
