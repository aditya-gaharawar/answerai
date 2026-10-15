export type PromptSuggestion = { content: string; title?: string | string[] };
export type NormalizedPromptSuggestion = { content: string; title: string[] };
export function normalizePromptSuggestions(value: unknown): NormalizedPromptSuggestion[] {
	if (!Array.isArray(value)) throw new Error('Invalid prompt suggestions');
	return value.map((entry: unknown) => {
		if (
			!entry ||
			typeof entry !== 'object' ||
			!('content' in entry) ||
			typeof entry.content !== 'string'
		)
			throw new Error('Invalid prompt suggestion');
		const title = 'title' in entry ? entry.title : undefined;
		if (
			title != null &&
			typeof title !== 'string' &&
			!(Array.isArray(title) && title.every((part) => typeof part === 'string'))
		)
			throw new Error('Invalid prompt title');
		return {
			content: entry.content,
			title: typeof title === 'string' ? [title, ''] : Array.isArray(title) ? [...title] : ['', '']
		};
	});
}
