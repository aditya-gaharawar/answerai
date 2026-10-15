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
	output?: unknown;
	tool_calls?: unknown;
	files?: unknown[];
};
