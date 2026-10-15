import { describe, expect, it } from 'vitest';
import { convertMessagesToHistory, createMessagesList, getDeepestChildId } from './chatHistory';

describe('chat graph safety', () => {
	it('keeps explicit root branches and safely stores prototype-like IDs', () => {
		const history = convertMessagesToHistory([
			{ id: '__proto__', role: 'user', parentId: null },
			{ id: 'second', role: 'user', parentId: null }
		]);
		expect(Object.getPrototypeOf(history.messages)).toBeNull();
		expect(history.messages.second.parentId).toBeNull();
		expect(history.messages.__proto__.childrenIds).toEqual([]);
	});
	it('stops on cyclic parent links instead of freezing the browser', () => {
		const history = convertMessagesToHistory([
			{ id: 'a', parentId: 'b' },
			{ id: 'b', parentId: 'a' }
		]);
		expect(createMessagesList(history, 'a').map((node) => node.id)).toEqual(['b', 'a']);
	});
	it('does not navigate to a dangling child', () => {
		const history = convertMessagesToHistory([{ id: 'a' }]);
		history.messages.a.childrenIds = ['missing'];
		expect(getDeepestChildId(history, 'a')).toBe('a');
	});
});
