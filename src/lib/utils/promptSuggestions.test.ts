import { expect, it } from 'vitest';
import { normalizePromptSuggestions } from './promptSuggestions';
it('normalizes legacy titles without modifying the source', () => {
	const source = [{ content: 'one', title: 'Title' }, { content: 'two' }];
	expect(normalizePromptSuggestions(source)).toEqual([
		{ content: 'one', title: ['Title', ''] },
		{ content: 'two', title: ['', ''] }
	]);
	expect(source[0].title).toBe('Title');
});
it('rejects malformed entries before returning a partially imported list', () => {
	expect(() =>
		normalizePromptSuggestions([{ content: 'valid' }, { content: 'bad', title: [1] }])
	).toThrow();
	expect(() => normalizePromptSuggestions({})).toThrow();
});
