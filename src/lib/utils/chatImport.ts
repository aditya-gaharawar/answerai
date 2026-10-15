import { convertMessagesToHistory } from './chatHistory';
import type { HistoryNode } from './chatHistory';
const record = (value: unknown): value is Record<string, unknown> =>
	!!value && typeof value === 'object' && !Array.isArray(value);
const timestamp = (value: unknown): number | null =>
	typeof value === 'number' && Number.isFinite(value) ? Math.floor(value) : null;
export const getImportOrigin = (chats: unknown): 'openai' | 'webui' =>
	Array.isArray(chats) && chats.some((chat) => record(chat) && Object.hasOwn(chat, 'mapping'))
		? 'openai'
		: 'webui';

function messageContent(message: Record<string, unknown>): string {
	if (!record(message.content)) return '';
	const parts = Array.isArray(message.content.parts)
		? message.content.parts.filter((part): part is string => typeof part === 'string')
		: [];
	return parts.length
		? parts.join('\n')
		: typeof message.content.text === 'string'
			? message.content.text
			: '';
}
function convertConversation(conversation: Record<string, unknown>) {
	if (!record(conversation.mapping)) return null;
	const messages: Partial<HistoryNode>[] = [];
	const models = new Set<string>();
	for (const [id, entry] of Object.entries(conversation.mapping)) {
		if (!record(entry) || !record(entry.message)) continue;
		const message = entry.message;
		const role = record(message.author) ? message.author.role : undefined;
		if (role !== 'user' && role !== 'assistant') continue;
		const content = messageContent(message);
		if (!messages.length && !content) continue;
		const metadata = record(message.metadata) ? message.metadata : {};
		const model = typeof metadata.model_slug === 'string' ? metadata.model_slug : 'gpt-3.5-turbo';
		if (role === 'assistant') models.add(model);
		messages.push({
			id,
			role,
			content,
			model,
			done: true,
			context: null,
			...(timestamp(message.create_time) !== null
				? { timestamp: timestamp(message.create_time) ?? undefined }
				: {})
		});
	}
	if (!messages.length) return null;
	const history = convertMessagesToHistory(messages);
	return {
		history,
		models: models.size ? [...models] : ['gpt-3.5-turbo'],
		messages: Object.values(history.messages),
		options: {},
		timestamp: timestamp(conversation.create_time),
		title: typeof conversation.title === 'string' ? conversation.title : 'New Chat'
	};
}
export function convertOpenAIChats(chats: unknown) {
	const result: {
		id?: string;
		user_id: string;
		title: string;
		chat: NonNullable<ReturnType<typeof convertConversation>>;
		created_at: number | null;
		updated_at: number | null;
	}[] = [];
	for (const entry of Array.isArray(chats) ? chats : []) {
		if (!record(entry)) continue;
		const chat = convertConversation(entry);
		if (!chat) continue;
		const created = timestamp(entry.create_time);
		result.push({
			...(typeof entry.id === 'string' ? { id: entry.id } : {}),
			user_id: '',
			title: chat.title,
			chat,
			created_at: created,
			updated_at: timestamp(entry.update_time) ?? created
		});
	}
	return result;
}
