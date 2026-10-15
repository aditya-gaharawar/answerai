import { describe, it, expect } from 'vitest';
import { buildFolderTree } from './folderTree';
const folder = (id: string, parent_id: string | null = null, updated_at = 1) => ({
	id,
	name: id,
	parent_id,
	updated_at,
	created_at: 1
});
describe('folder graph repair', () => {
	it('breaks cycles and puts missing-parent folders at the root without mutating responses', () => {
		const owned = [folder('a', 'b'), folder('b', 'a'), folder('orphan', 'missing')];
		const result = buildFolderTree(owned, []);
		expect(result.b.parent_id).toBe(null);
		expect(result.orphan.parent_id).toBe(null);
		expect(owned[1].parent_id).toBe('a');
	});
	it('merges shared folders, sorts children and supports prototype-like IDs', () => {
		const result = buildFolderTree(
			[folder('__proto__'), folder('old', '__proto__', 1)],
			[folder('__proto__'), folder('new', '__proto__', 2)],
			'old'
		);
		expect(Object.getPrototypeOf(result)).toBe(null);
		expect(result.__proto__.childrenIds).toEqual(['new', 'old']);
		expect(result.__proto__.showOwnerInfo).toBe(true);
		expect(result.new.shared).toBe(true);
		expect(result.old.new).toBe(true);
	});
});
