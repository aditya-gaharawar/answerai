import { writable, type Writable } from 'svelte/store';
/** Keep identifiers such as __proto__ and constructor as ordinary dictionary keys. */
export function recordStore<T>(): Writable<Record<string, T | undefined>> {
	const copy = (value: Record<string, T | undefined>): Record<string, T | undefined> =>
		Object.assign(Object.create(null), value);
	const store = writable<Record<string, T | undefined>>(Object.create(null));
	return {
		subscribe: store.subscribe,
		set(value) {
			store.set(copy(value));
		},
		update(updater) {
			store.update((value) => copy(updater(value)));
		}
	};
}
