export interface OpenAIConnectionOptions {
	enable?: boolean;
	model_ids?: string[];
	prefix_id?: string;
	tags?: (string | { name: string })[];
	name?: string;
	auth_type?: string;
	connection_type?: string;
	api_type?: string;
	api_version?: string;
	[key: string]: unknown;
}
export interface OpenAIConnections {
	OPENAI_API_BASE_URLS: string[];
	OPENAI_API_KEYS: string[];
	OPENAI_API_CONFIGS: Record<string, OpenAIConnectionOptions>;
}

export type ToolServerData = {
	config?: { enable?: boolean };
	url: string;
	id?: string;
	openapi?: Record<string, unknown>;
	info?: { name?: string; title?: string; description?: string; version?: string };
	specs?: import('$lib/utils/openApiSchema').ToolPayload[];
	system_prompt?: string;
	error?: unknown;
};

export type ModelConnection = {
	url: string;
	key: string;
	config: OpenAIConnectionOptions & { key?: string };
};
export type ToolConnection = import('$lib/stores').ServerConnection & {
	type?: string;
	info?: { id?: string; name?: string; description?: string };
};
