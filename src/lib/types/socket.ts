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
