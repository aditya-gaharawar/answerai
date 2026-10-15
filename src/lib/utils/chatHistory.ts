import { v4 as uuidv4 } from 'uuid';

export interface HistoryNode {
	id: string;
	parentId: string | null;
	childrenIds: string[];
	role: string;
	content: string;
	annotation?: import('$lib/types/messages').MessageAnnotation;
	output?: import('$lib/components/chat/Messages/structuredOutput').OutputItem[];
	files?: (Omit<import('$lib/types/notes').NoteAttachment, 'id'> & { id?: string | null })[];
	timestamp?: number;
	model?: string;
	modelIdx?: number;
	models?: string[];
	selectedModelId?: string;
	merged?: { status: boolean; content: string; timestamp?: number };
	usage?: unknown;
	info?: { usage?: unknown; [key: string]: unknown };
	error?: unknown;
	ttsSentContentPartCount?: number;
	done?: boolean;
	[key: string]: unknown;
}
export interface ChatHistory<T extends HistoryNode = HistoryNode> {
	messages: Record<string, T>;
	currentId: string | null;
}

export const convertMessagesToHistory = (messages: Partial<HistoryNode>[]): ChatHistory => {
	const history: ChatHistory = {
		messages: Object.create(null),
		currentId: null
	};

	let parentMessageId: string | null = null;
	let messageId: string | null = null;

	for (const message of messages) {
		messageId = typeof message.id === 'string' && message.id ? message.id : uuidv4();
		const parentId = message.parentId === undefined ? parentMessageId : message.parentId;

		history.messages[messageId] = {
			...message,
			id: messageId,
			role: message.role ?? 'user',
			content: message.content ?? '',
			parentId,
			childrenIds: []
		};

		parentMessageId = messageId;
	}

	for (const message of Object.values(history.messages)) {
		if (message.parentId && history.messages[message.parentId]) {
			history.messages[message.parentId].childrenIds = [
				...history.messages[message.parentId].childrenIds,
				message.id
			];
		}
	}

	history.currentId = messageId;
	return history;
};

// Repair structurally-malformed history nodes from failed regenerations.
// A lost assistant placeholder may exist under its map key with only
// completion fields (content/done/error), missing id/role/parentId.
// Reconstruct graph fields so already-corrupted chats recover on open.
export const sanitizeHistory = (history: ChatHistory | null | undefined) => {
	if (!history?.messages || typeof history.messages !== 'object') return;

	// Purge entries that aren't usable objects
	for (const [id, message] of Object.entries(history.messages)) {
		if (!message || typeof message !== 'object') {
			delete history.messages[id];
		}
	}

	// Ensure every surviving node has its canonical id and a childrenIds array
	for (const [id, message] of Object.entries(history.messages)) {
		if (message.id !== id) message.id = id;
		if (!Array.isArray(message.childrenIds)) message.childrenIds = [];
		else message.childrenIds = message.childrenIds.filter((id) => typeof id === 'string');
		if (message.parentId != null && typeof message.parentId !== 'string') message.parentId = null;
		if (typeof message.role !== 'string') message.role = '';
	}

	// Build reverse lookup: parent, indexed by child id
	const parentByChildId: Record<string, string> = Object.create(null);
	for (const [id, message] of Object.entries(history.messages)) {
		for (const childId of message.childrenIds) {
			parentByChildId[childId] = id;
		}
	}

	// Recover currentId before role reconstruction can make a malformed node
	// look valid.
	const currentMessage = history.currentId ? history.messages[history.currentId] : undefined;
	if (!currentMessage?.id || !currentMessage?.role) {
		let latestLeafId = null;
		let latestTimestamp = -1;

		for (const [id, message] of Object.entries(history.messages)) {
			if (message.childrenIds.length === 0 && (message.timestamp ?? 0) > latestTimestamp) {
				latestLeafId = id;
				latestTimestamp = message.timestamp ?? 0;
			}
		}

		history.currentId = latestLeafId ?? Object.keys(history.messages)[0] ?? null;
	}

	// Reconstruct missing parentId and role
	for (const [id, message] of Object.entries(history.messages)) {
		if (message.parentId && !history.messages[message.parentId]) message.parentId = null;
		// Well-formed: has role and explicit parentId (null is valid for root)
		if (message.role && message.parentId !== undefined) continue;

		if (message.parentId === undefined) {
			message.parentId = parentByChildId[id] ?? null;
		}

		if (!message.role) {
			const parent = message.parentId ? history.messages[message.parentId] : null;
			message.role =
				parent?.role === 'user'
					? 'assistant'
					: parent?.role === 'assistant'
						? 'user'
						: message.model || message.usage || message.done !== undefined
							? 'assistant'
							: 'user';
		}
	}

	// Prune childrenIds referencing deleted/missing nodes
	for (const message of Object.values(history.messages)) {
		message.childrenIds = message.childrenIds.filter((childId) => history.messages[childId]);
	}
};

export const createMessagesList = <T extends HistoryNode>(
	history: ChatHistory<T>,
	messageId: string | null | undefined
): T[] => {
	const list: T[] = [];
	const visited = new Set<string>();
	let currentId = messageId;

	while (currentId !== null && currentId !== undefined) {
		if (visited.has(currentId)) break;
		visited.add(currentId);
		const message = history.messages[currentId];
		if (message === undefined) {
			break;
		}
		list.push(message);
		currentId = message.parentId;
	}

	return list.reverse();
};

export const getDeepestChildId = (
	history: ChatHistory,
	messageId: string | null
): string | null => {
	let deepestId = messageId;
	const visitedMessageIds = new Set([deepestId]);
	let childrenIds =
		deepestId === null
			? Object.keys(history.messages).filter((id) => history.messages[id].parentId === null)
			: (history.messages[deepestId]?.childrenIds ?? []);

	while (childrenIds.length !== 0) {
		const childId = childrenIds.at(-1);
		if (!childId || !history.messages[childId]) break;
		if (visitedMessageIds.has(childId)) {
			console.warn('Circular dependency detected in message history', childId);
			break;
		}

		visitedMessageIds.add(childId);
		deepestId = childId;
		childrenIds = history.messages[deepestId]?.childrenIds ?? [];
	}

	return deepestId;
};
