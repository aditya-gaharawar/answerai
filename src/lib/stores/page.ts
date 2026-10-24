import { page as state } from '$app/state';
import { toStore, type Readable } from 'svelte/store';

// Keep legacy Svelte components reactive during client-side navigation. Reading
// each field inside toStore tracks SvelteKit's rune-backed page state.
const readPage = () => ({
	data: state.data,
	error: state.error,
	form: state.form,
	params: state.params,
	route: state.route,
	state: state.state,
	status: state.status,
	url: state.url
});

// Create subscriptions lazily so server rendering never caches another request.
export const page: Readable<ReturnType<typeof readPage>> = {
	subscribe(run, invalidate) {
		return toStore(readPage).subscribe(run, invalidate);
	}
};
