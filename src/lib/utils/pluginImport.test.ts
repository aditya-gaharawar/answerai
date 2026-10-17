import { expect, it } from 'vitest';
import { parsePluginDraft } from './pluginImport';
it('normalizes a legacy draft without an ID or metadata', () => {
	expect(parsePluginDraft('{"name":"Example","content":"print(1)"}')).toMatchObject({
		id: '',
		name: 'Example',
		content: 'print(1)',
		meta: { description: '' }
	});
});
it.each([
	null,
	[],
	{ content: 1 },
	{ content: '', meta: { i18n: { en: { name: 12 } } } },
	{
		content: '',
		access_grants: [{ principal_type: 'user', principal_id: '*', permission: 'admin' }]
	}
])('rejects malformed editor input before it reaches a component', (value) => {
	expect(() => parsePluginDraft(value)).toThrow();
});
it('keeps valid translations and permissions', () => {
	const draft = {
		id: 'example',
		name: 'Example',
		content: '',
		meta: { description: 'Test', i18n: { en: { name: 'Example' } } },
		access_grants: [{ principal_type: 'user', principal_id: '*', permission: 'read' }]
	};
	expect(parsePluginDraft(draft)).toEqual(draft);
});
it('preserves prototype-like locale names without changing the dictionary prototype', () => {
	const draft = parsePluginDraft('{"content":"","meta":{"i18n":{"__proto__":{"name":"Example"}}}}');
	if (!draft.meta.i18n) throw new Error('Missing imported translations');
	expect(Object.hasOwn(draft.meta.i18n, '__proto__')).toBe(true);
	expect(Object.getPrototypeOf(draft.meta.i18n)).toBe(Object.prototype);
});
it('rejects permission principals represented by objects', () => {
	expect(() =>
		parsePluginDraft({
			content: '',
			access_grants: [
				{ principal_type: { toString: () => 'user' }, principal_id: '*', permission: 'read' }
			]
		})
	).toThrow('Invalid plugin permissions');
});
