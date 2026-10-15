// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
	class AudioWorkletProcessor {
		readonly port: MessagePort;
	}
	function registerProcessor(name: string, processor: typeof AudioWorkletProcessor): void;

	const APP_VERSION: string;
	const APP_BUILD_HASH: string;
	const APP_BUILD_CHANNEL: 'main' | 'dev' | 'unknown';

	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface Platform {}
	}
}

export {};

// The root layout provides this store through setContext('i18n', i18n).
// Keep the named context contract visible to every consumer without assertions.
declare module 'svelte' {
	export function getContext(key: 'i18n'): typeof import('$lib/i18n').i18n;
}

// Files shared by the editor's image node views and collaboration updates.
declare module '@tiptap/core' {
	interface Storage {
		files?: import('$lib/types/notes').NoteAttachment[];
	}
}
