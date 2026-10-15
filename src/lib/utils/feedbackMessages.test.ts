import { expect, it } from 'vitest';
import { feedbackMessages } from './feedbackMessages';
it('handles feedback whose snapshot was removed or contains missing messages', () => {
	for (const value of [null, {}, { meta: { message_id: 'x' }, snapshot: {} }])
		expect(feedbackMessages(value)).toEqual({ prompt: '', response: '' });
});
it('reads only the selected response and its direct parent', () => {
	expect(
		feedbackMessages({
			meta: { message_id: 'b' },
			snapshot: {
				chat: {
					chat: {
						history: {
							messages: { a: { content: 'question' }, b: { content: 'answer', parentId: 'a' } }
						}
					}
				}
			}
		})
	).toEqual({ prompt: 'question', response: 'answer' });
});
