import { describe, it, expect } from 'vitest';
import { convertOpenAIChats, getImportOrigin } from './chatImport';
describe('conversation import', () => {
	it('keeps the history cursor and children on imported messages after skipping tool nodes', () => {
		const result = convertOpenAIChats([
			{
				id: 'c',
				title: 'Chat',
				create_time: 12.9,
				mapping: {
					root: { message: { author: { role: 'user' }, content: { parts: ['Question'] } } },
					reply: {
						message: {
							author: { role: 'assistant' },
							content: { parts: [{ image: 'x' }, 'Answer'] }
						}
					},
					tool: { message: { author: { role: 'tool' }, content: { parts: ['Hidden'] } } }
				}
			}
		]);
		const chat = result[0].chat;
		expect(chat.history.currentId).toBe('reply');
		expect(chat.history.messages.root.childrenIds).toEqual(['reply']);
		expect(chat.history.messages.reply.childrenIds).toEqual([]);
		expect(result[0].created_at).toBe(12);
	});
	it('handles malformed and metadata-only entries without crashing', () => {
		expect(
			convertOpenAIChats([
				null,
				4,
				{ title: 'Folder' },
				{ mapping: null },
				{ mapping: { x: { message: null } } }
			])
		).toEqual([]);
		expect(getImportOrigin([null, { mapping: {} }])).toBe('openai');
		expect(getImportOrigin(null)).toBe('webui');
	});
	it('accepts prototype-like IDs and text fallback content', () => {
		const mapping = JSON.parse(
			'{"__proto__":{"message":{"author":{"role":"user"},"content":{"text":"hello"}}}}'
		);
		const chat = convertOpenAIChats([{ mapping }])[0].chat;
		expect(chat.history.messages.__proto__.content).toBe('hello');
		expect(Object.getPrototypeOf(chat.history.messages)).toBe(null);
	});
});
