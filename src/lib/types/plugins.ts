import type { AccessGrant } from '$lib/apis';

export interface PluginManifest {
	author?: string;
	author_url?: string;
	funding_url?: string;
	version?: string;
	required_answerai_version?: string;
	requirements?: string;
	[key: string]: unknown;
}
export interface PluginMeta {
	description?: string | null;
	manifest?: PluginManifest | null;
	has_user_valves?: boolean;
	toggle?: boolean;
	i18n?: Record<string, Record<string, string>> | null;
	[key: string]: unknown;
}
export interface PluginOwner {
	username?: string;
	id: string;
	name: string;
	email?: string;
	profile_image_url?: string;
}
export interface FunctionSummary {
	id: string;
	name: string;
	type: string;
	meta: PluginMeta;
	user_id?: string | null;
	user?: PluginOwner | null;
	content?: string;
	is_active?: boolean;
	is_global?: boolean;
	has_user_valves?: boolean;
	updated_at?: number;
	created_at?: number;
}
export interface ToolSummary {
	authenticated?: boolean;
	id: string;
	name: string;
	meta: PluginMeta;
	user_id?: string | null;
	user?: PluginOwner | null;
	content?: string | null;
	specs?: { name: string; description?: string; parameters?: Record<string, unknown> }[];
	access_grants?: AccessGrant[];
	updated_at?: number;
	created_at?: number;
	write_access?: boolean;
	has_user_valves?: boolean;
}
