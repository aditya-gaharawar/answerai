import type { JSONContent } from '@tiptap/core';
export type EditorContent = { html: string; md: string; json: JSONContent | '' };
export type SuggestionCommand = { id: string; label?: string; type?: string; content?: string };
export type EditorSuggestion = Omit<
	Partial<import('@tiptap/suggestion').SuggestionOptions<SuggestionCommand, SuggestionCommand>>,
	'editor'
> & { char: string };
export type SuggestionSelection =
	| { type: 'model'; data: import('$lib/stores').Model }
	| { type: 'skill'; data: { id: string; name: string } };
export type SuggestionUpload =
	| {
			type: 'file' | 'filesystem';
			data: {
				id: string;
				name?: string;
				type?: string;
				path?: string;
				url?: string;
				size?: number;
			};
	  }
	| { type: 'web'; data: string };
export type SuggestionRendererProps = {
	i18n?: unknown;
	onSelect?: (selection: SuggestionSelection) => void;
	onUpload?: (upload: SuggestionUpload) => void;
	insertTextHandler?: (text: string) => void;
	[key: string]: unknown;
};
