declare module '@sveltejs/svelte-virtual-list' {
	import { SvelteComponent } from 'svelte';
	export default class VirtualList<T> extends SvelteComponent<
		{ items: T[]; height?: string; itemHeight?: number; start?: number; end?: number },
		Record<string, never>,
		{ default: { item: T; index: number } }
	> {}
}

declare module '@joplin/turndown-plugin-gfm' {
	import TurndownService from 'turndown';
	type Plugin = (service: TurndownService) => void;
	export const gfm: Plugin;
	export const tables: Plugin;
	export const strikethrough: Plugin;
	export const highlightedCodeBlock: Plugin;
}
