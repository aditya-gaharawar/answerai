import type { CompletionEvent } from './messages';
export type SocketReply = (value: unknown) => void;
export type ToolParams = Record<string, unknown> & {
	path?: string;
	page?: number;
	inline?: boolean;
};
export type TerminalFileResult = {
	path?: string;
	name?: string;
	content_type?: string;
	mime_type?: string;
	full_path?: string;
	page?: number;
	exists?: boolean;
	[key: string]: unknown;
};
export type ToolExecutionRequest = {
	session_id?: string;
	name: string;
	server?: { url: string };
	params?: ToolParams;
};
type SessionPayload<T> = T & { session_id?: string };
export type RootChatEvent = {
	chat_id: string;
	shared?: boolean;
	internal?: boolean;
	data:
		| { type: 'request:terminal:state'; data: SessionPayload<{ terminal_id: string }> }
		| { type: 'calendar:alert'; data: SessionPayload<{ title: string; minutes_until: number }> }
		| {
				type: 'execute:python';
				data: SessionPayload<{
					id: string;
					code: string;
					files?: { id?: string; filename?: string; name?: string }[];
				}>;
		  }
		| { type: 'execute:tool'; data: ToolExecutionRequest }
		| { type: 'request:terminal'; data: SessionPayload<{ terminal_id: string; path: string }> }
		| {
				type: 'request:chat:completion';
				data: SessionPayload<{
					channel: string;
					model: { urlIdx: number };
					form_data: { model: string; stream?: boolean; [key: string]: unknown };
				}>;
		  }
		| { type: 'chat:completion'; data: SessionPayload<CompletionEvent & { title?: string }> }
		| { type: 'chat:title' | 'chat:tags'; data: SessionPayload<Record<string, unknown>> };
};
export type SyncStatsEvent = {
	requestId?: string;
	lastSyncedChatUpdatedAt?: number;
	searchParams?: { updated_at?: number; [key: string]: string | number | undefined };
};

export type ChannelNotificationEvent = {
	channel_id: string;
	created_at: number;
	user?: import('./channels').ChannelUser | null;
	channel?: { name?: string; type?: string | null };
	data:
		| { type: 'channel:mute'; data: { is_channel_muted: boolean } }
		| { type: 'channel:created'; data: unknown }
		| { type: 'typing'; data: unknown }
		| {
				type: 'message' | 'message:update' | 'message:delete' | 'message:reply';
				data: import('./channels').ChannelMessage;
		  };
};

/** Payloads emitted by the chat socket protocol. */
type InteractionPayload = { interaction_id?: string; tool_call?: unknown; [key: string]: unknown };
type ChatEventPayloads = {
	'voice:play_animation': { name?: string; model_id?: string };
	'request:interaction:done': { interaction_id?: string };
	'request:user_input': InteractionPayload;
	'request:elicitation': InteractionPayload;
	confirmation: InteractionPayload & { title: string; message: string };
	typing: { typing: boolean };
	'chat:messages': import('$lib/utils/chatHistory').ChatHistory;
	'chat:access': { active?: boolean };
	'chat:active': { active: boolean };
	'chat:reload': unknown;
	'chat:list': unknown;
	status: import('./messages').MessageStatus;
	context_compaction: import('./messages').MessageStatus & { error?: unknown };
	'response:completion': Parameters<
		typeof import('$lib/components/chat/Messages/structuredOutput').applyResponseStreamEvent
	>[1];
	'chat:completion': import('./messages').CompletionEvent;
	'chat:tasks:cancel': {
		output?: import('$lib/components/chat/Messages/structuredOutput').OutputItem[];
	};
	'chat:message:delta': { content: string };
	message: { content: string };
	'chat:message': { content: string };
	replace: { content: string };
	'chat:message:voice': { voice: unknown };
	'chat:message:files': { files: import('./notes').NoteAttachment[] };
	files: { files: import('./notes').NoteAttachment[] };
	'chat:message:tasks': { tasks: import('./chat').ChatTask[] };
	'chat:message:embeds': { embeds: string[] };
	embeds: { embeds: string[] };
	'chat:message:error': { error: unknown };
	'chat:message:follow_ups': { follow_ups: string[] };
	'chat:outlet': {
		messages?: (Partial<import('$lib/utils/chatHistory').HistoryNode> & { id: string })[];
	};
	'chat:message:favorite': { favorite: boolean };
	'chat:title': string;
	'chat:tags': unknown;
	source:
		| (import('./messages').CodeExecution & { type: 'code_execution' })
		| { type?: 'source' | 'citation'; [key: string]: unknown };
	citation: ChatEventPayloads['source'];
	notification: { type?: string; content?: string };
	execute: { code: string };
	input: {
		title: string;
		message: string;
		placeholder: string;
		value?: string;
		input?: { type?: string; options?: (string | { label?: string; value: string })[] };
		type?: string;
		options?: (string | { label?: string; value: string })[];
	};
};
type ChatEventData =
	| {
			[K in keyof ChatEventPayloads]: { type: K; data: ChatEventPayloads[K] };
	  }[keyof ChatEventPayloads]
	| { type: `terminal:${string}`; data: { path?: string; page?: number } };
export type ChatSocketEvent = {
	chat_id: string;
	message_id?: string;
	user_id?: string;
	shared?: boolean;
	user?: { id: string; name: string };
	data: ChatEventData;
};
