import { expect, it } from 'vitest';
import { groupCitations } from './citations';
it('keeps metadata and scores aligned when earlier documents lack them', () => {
	const result = groupCitations([
		{
			source: { id: 42 },
			document: ['first', 'second'],
			metadata: [null, { source: 42, page: 3 }],
			distances: [null, 0.5]
		}
	]);
	expect(result).toHaveLength(1);
	expect(result[0].id).toBe('42');
	expect(result[0].metadata[0]).toBeUndefined();
	expect(result[0].metadata[1]?.page).toBe(3);
	expect(result[0].distances).toEqual([undefined, 0.5]);
});
it('ignores malformed documents and supplies a usable source label', () => {
	expect(groupCitations([null, {}, { document: [null, 'text'] }])[0].source.name).toBe('N/A');
});
