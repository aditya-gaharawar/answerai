const record = (value: unknown): value is Record<string, unknown> =>
	!!value && typeof value === 'object' && !Array.isArray(value);
export function feedbackMessages(feedback: unknown): { prompt: string; response: string } {
	if (
		!record(feedback) ||
		!record(feedback.meta) ||
		typeof feedback.meta.message_id !== 'string' ||
		!record(feedback.snapshot)
	)
		return { prompt: '', response: '' };
	const outer = feedback.snapshot.chat;
	const chat = record(outer) ? outer.chat : null;
	const history = record(chat) ? chat.history : null;
	const messages = record(history) ? history.messages : null;
	if (!record(messages)) return { prompt: '', response: '' };
	const response = messages[feedback.meta.message_id];
	const parent =
		record(response) && typeof response.parentId === 'string' ? messages[response.parentId] : null;
	return {
		prompt: record(parent) && typeof parent.content === 'string' ? parent.content : '',
		response: record(response) && typeof response.content === 'string' ? response.content : ''
	};
}
