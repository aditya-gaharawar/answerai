import { it, expect } from 'vitest';
import { get } from 'svelte/store';
import {
	MODEL_DOWNLOAD_POOL,
	updateModelDownload,
	removeModelDownload,
	cancelModelDownload
} from './modelDownloads';
it('ignores late progress and cleanup from cancelled or replaced downloads', () => {
	const old = new AbortController();
	const current = new AbortController();
	MODEL_DOWNLOAD_POOL.set({ model: { model: 'model', abortController: old } });
	old.abort();
	updateModelDownload('model', old, { done: true });
	expect(get(MODEL_DOWNLOAD_POOL).model?.done).not.toBe(true);
	MODEL_DOWNLOAD_POOL.set({ model: { model: 'model', abortController: current } });
	updateModelDownload('model', old, { pullProgress: 100 });
	removeModelDownload('model', old);
	expect(get(MODEL_DOWNLOAD_POOL).model?.abortController).toBe(current);
	updateModelDownload('model', current, { pullProgress: 30 });
	expect(get(MODEL_DOWNLOAD_POOL).model?.pullProgress).toBe(30);
	removeModelDownload('model', current);
	expect(get(MODEL_DOWNLOAD_POOL).model).toBeUndefined();
});

it('clears a cancelled row even when reader cancellation fails, preserving a replacement', async () => {
	const controller = new AbortController();
	let rejectCancel!: (reason: Error) => void;
	const reader = new ReadableStream<string>({
		cancel: () =>
			new Promise<void>((_, reject) => {
				rejectCancel = reject;
			})
	}).getReader();
	MODEL_DOWNLOAD_POOL.set({ model: { model: 'old', abortController: controller, reader } });
	const cancelled = cancelModelDownload('model');
	expect(controller.signal.aborted).toBe(true);
	expect(get(MODEL_DOWNLOAD_POOL).model).toBeUndefined();
	const replacement = new AbortController();
	MODEL_DOWNLOAD_POOL.set({ model: { model: 'new', abortController: replacement } });
	rejectCancel(new Error('request aborted'));
	await expect(cancelled).resolves.toMatchObject({ model: 'old' });
	expect(get(MODEL_DOWNLOAD_POOL).model?.abortController).toBe(replacement);
});
