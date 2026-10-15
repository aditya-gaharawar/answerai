import { expect, it } from 'vitest';
import { normalizeDirectModels } from './directModels';

it('accepts both model-list response shapes and preserves the provider ID behind a prefix', () => {
	const model = normalizeDirectModels(
		{ data: [{ id: 'gpt-example' }] },
		{ prefix_id: 'work', tags: [' local '] },
		'2'
	)[0];
	expect(model).toMatchObject({
		id: 'work.gpt-example',
		openai: { id: 'gpt-example' },
		urlIdx: '2',
		tags: [{ name: 'local' }]
	});
	expect(normalizeDirectModels([{ id: 'model' }], {}, '0')).toHaveLength(1);
});
it('ignores malformed provider entries without crashing model selection', () => {
	expect(normalizeDirectModels({ data: {} }, {}, '0')).toEqual([]);
	expect(
		normalizeDirectModels([null, {}, { id: 42 }, { id: '' }, { id: 'valid' }], {}, '0').map(
			(model) => model.id
		)
	).toEqual(['valid']);
});
