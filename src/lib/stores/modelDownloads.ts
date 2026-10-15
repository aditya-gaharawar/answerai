import { get } from 'svelte/store';
import { recordStore } from './recordStore';
export type ModelDownload = {
	model: string;
	abortController?: AbortController | null;
	reader?: ReadableStreamDefaultReader<string>;
	done?: boolean;
	pullProgress?: number;
	digest?: string;
	providerLabel?: string;
};
export const MODEL_DOWNLOAD_POOL = recordStore<ModelDownload>();
export function updateModelDownload(
	key: string,
	controller: AbortController | null | undefined,
	patch: Partial<ModelDownload>
): void {
	if (!controller || controller.signal.aborted) return;
	MODEL_DOWNLOAD_POOL.update((rows) => {
		const existing = rows[key];
		if (!existing || existing.abortController !== controller) return rows;
		return { ...rows, [key]: { ...existing, ...patch } };
	});
}
export function removeModelDownload(
	key: string,
	controller: AbortController | null | undefined
): void {
	MODEL_DOWNLOAD_POOL.update((rows) => {
		if (rows[key]?.abortController !== controller) return rows;
		const result = { ...rows };
		delete result[key];
		return result;
	});
}

/** Remove the captured job before aborting, so late cleanup cannot remove its replacement. */
export async function cancelModelDownload(key: string): Promise<ModelDownload | undefined> {
	const download = get(MODEL_DOWNLOAD_POOL)[key];
	if (!download) return;
	removeModelDownload(key, download.abortController);
	download.abortController?.abort();
	try {
		await download.reader?.cancel();
	} catch {
		// Aborting the request can reject an already pending stream cancellation.
	}
	return download;
}
