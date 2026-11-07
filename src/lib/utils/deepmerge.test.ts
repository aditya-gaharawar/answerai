import { describe, expect, it } from 'vitest';
import deepmerge from 'deepmerge';

describe('vendored deepmerge', () => {
	it('retains nested merge, arrays and custom array behavior', () => {
		expect(deepmerge({ nested: { a: 1 }, items: [1] }, { nested: { b: 2 }, items: [2] })).toEqual({
			nested: { a: 1, b: 2 },
			items: [1, 2]
		});
		expect(
			deepmerge({ items: [1] }, { items: [2] }, { arrayMerge: (_target, source) => source })
		).toEqual({ items: [2] });
	});
	it.each(['target', 'source'])(
		'keeps the normal result prototype with hostile JSON in %s',
		(side) => {
			const hostile = JSON.parse(
				'{"__proto__":{"polluted":true},"nested":{"__proto__":{"nestedPolluted":true}}}'
			);
			const result =
				side === 'target'
					? deepmerge(hostile, { safe: true })
					: deepmerge(Object.create(null), hostile);
			expect(Object.getPrototypeOf(result)).toBe(Object.prototype);
			expect((result as Record<string, unknown>).polluted).toBeUndefined();
			expect(Object.getPrototypeOf((result as { nested: object }).nested)).toBe(Object.prototype);
			expect(({} as Record<string, unknown>).polluted).toBeUndefined();
		}
	);
});
