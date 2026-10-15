import { it, expect } from 'vitest';
import { get } from 'svelte/store';
import { recordStore } from './recordStore';
it('preserves safe keys after replacement and reactive updates', () => {
	const store = recordStore<number>();
	store.set({ x: 1 });
	expect(get(store).constructor).toBeUndefined();
	store.update((value) => ({ ...value, ['__proto__']: 2 }));
	expect(get(store).__proto__).toBe(2);
	expect(Object.getPrototypeOf(get(store))).toBe(null);
});
