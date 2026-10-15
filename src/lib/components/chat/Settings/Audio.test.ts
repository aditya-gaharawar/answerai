// @vitest-environment happy-dom
import { expect, it, vi } from 'vitest';
import { mount, unmount, tick } from 'svelte';
import { get, writable } from 'svelte/store';
import Audio from './Audio.svelte';
import { settings } from '$lib/stores';
import { KokoroTTS } from 'kokoro-js';

vi.mock('kokoro-js', () => ({ KokoroTTS: { from_pretrained: vi.fn() } }));
it('shares an in-flight speech model load and disposes a model delivered after unmount', async () => {
	let resolveModel!: (model: KokoroTTS) => void;
	const pendingModel = new Promise<KokoroTTS>((resolve) => {
		resolveModel = resolve;
	});
	vi.mocked(KokoroTTS.from_pretrained).mockReturnValue(pendingModel);
	const dispose = vi.fn(async () => {});
	const synthesis = Object.assign(new EventTarget(), { getVoices: () => [] });
	vi.stubGlobal('speechSynthesis', synthesis);
	const previousSettings = get(settings);
	settings.set({ audio: { tts: { engine: 'browser-kokoro', engineConfig: { dtype: 'q8' } } } });
	const target = document.createElement('div');
	document.body.appendChild(target);
	const component = mount(Audio, {
		target,
		props: { saveSettings: () => {} },
		context: new Map([['i18n', writable({ t: (key: string) => key, language: 'en-US' })]])
	});
	try {
		await vi.waitFor(() => expect(KokoroTTS.from_pretrained).toHaveBeenCalledOnce());
		await unmount(component);
		resolveModel({ model: { dispose }, voices: {} } as unknown as KokoroTTS);
		await pendingModel;
		await tick();
		await vi.waitFor(() => expect(dispose).toHaveBeenCalledOnce());
	} finally {
		settings.set(previousSettings);
		target.remove();
		vi.unstubAllGlobals();
		vi.resetAllMocks();
	}
});
