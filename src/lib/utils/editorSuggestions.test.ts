import { it, expect } from 'vitest';
import { normalizeSuggestionCommand } from './editorSuggestions';
it('rejects empty mention IDs before command handlers use them', () => {
	expect(normalizeSuggestionCommand({ id: null, label: 'Missing' })).toBe(null);
	expect(
		normalizeSuggestionCommand({ id: 'x', label: null, type: 'prompt', content: 'hello' })
	).toEqual({ id: 'x', type: 'prompt', content: 'hello' });
});
