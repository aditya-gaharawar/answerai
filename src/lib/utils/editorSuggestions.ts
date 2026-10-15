import type { SuggestionCommand } from '$lib/types/editor';
export function normalizeSuggestionCommand(value: unknown): SuggestionCommand | null {
	if (!value || typeof value !== 'object' || !('id' in value) || typeof value.id !== 'string')
		return null;
	return {
		id: value.id,
		...('label' in value && typeof value.label === 'string' ? { label: value.label } : {}),
		...('type' in value && typeof value.type === 'string' ? { type: value.type } : {}),
		...('content' in value && typeof value.content === 'string' ? { content: value.content } : {})
	};
}
