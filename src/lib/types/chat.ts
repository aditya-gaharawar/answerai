import type { InputVariableDefinition } from '$lib/utils/inputVariables';

export interface ContextUsage {
	tokens: number;
	estimated_tokens: number;
	threshold: number | null;
	percent: number | null;
	source: string;
}
export type ChatTask = { id: string; content: string; status: string };
export type PendingOAuthTool = {
	id: string;
	name: string;
	serverId: string;
	authType: string | null;
};
export type ChatVariableField = InputVariableDefinition & { key: string };
export type ChatVariableSchema = { fields: ChatVariableField[] };
export type TokenEstimateMessage = {
	content?: unknown;
	info?: { usage?: unknown };
	output?: unknown;
	tool_calls?: unknown;
	files?: unknown[];
};

export interface ChatSummary {
	owner_name?: string | null;
	participants?: import('$lib/apis/folders').ChatParticipant[];
	user_id?: string;
	id: string;
	title: string;
	updated_at: number;
	created_at: number;
	last_read_at?: number | null;
	snippet?: string | null;
	active?: boolean;
	archived?: boolean;
	folder_id?: string | null;
	time_range?: string;
	[key: string]: unknown;
}

export type ChatReadState = {
	chat_id: string;
	last_read_at?: number;
	folder_unread_counts?: Record<string, number>;
};

export type PromptSelection = { type: 'prompt'; data: string };
