import { expect, it } from 'vitest';
import { collectSourceIds } from './sourceIds';

it('handles numeric or malformed citation metadata without crashing the response renderer', () => {
	expect(
		collectSourceIds([
			null,
			{ document: ['a', 'b'], metadata: [{ source: 42, name: 'file.txt' }, { source: 42 }] },
			{ document: ['c'], source: { id: 'https://example.com/page' } }
		])
	).toEqual(['file.txt', 'https://example.com/page']);
	expect(collectSourceIds({})).toEqual([]);
});
it('keeps disabled citation placeholders aligned with documents', () => {
	expect(collectSourceIds([{ document: ['a', 'b'] }], false)).toEqual(['N/A', 'N/A']);
});
