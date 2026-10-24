// @vitest-environment happy-dom
import { expect, it, vi } from 'vitest';
import { tick } from 'svelte';

vi.mock('$app/state', async () => {
	const { SvelteMap } = await import('svelte/reactivity');
	const values = new SvelteMap<string, unknown>([
		['url', new URL('https://answerai.in/c/first')],
		['params', { id: 'first' }]
	]);
	return {
		page: {
			get url() {
				return values.get('url');
			},
			get params() {
				return values.get('params');
			},
			data: {},
			error: null,
			form: null,
			route: { id: '/c/[id]' },
			state: {},
			status: 200
		},
		values
	};
});

it('updates legacy page subscribers after navigation and stops after unsubscribe', async () => {
	const { page } = await import('./page');
	const { values } = (await import('$app/state')) as unknown as {
		values: Map<string, unknown>;
	};
	const seen: string[] = [];
	const stop = page.subscribe((value) => seen.push(`${value.params.id}:${value.url.pathname}`));
	values.set('params', { id: 'second' });
	values.set('url', new URL('https://answerai.in/c/second'));
	await tick();
	expect(seen.at(-1)).toBe('second:/c/second');
	stop();
	const count = seen.length;
	values.set('params', { id: 'third' });
	await tick();
	expect(seen).toHaveLength(count);
});
