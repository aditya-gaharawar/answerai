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
