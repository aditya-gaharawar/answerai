import type { AccessGrant } from '$lib/apis';
export type ArenaConfigModel = {
	id: string;
	name: string;
	meta: {
		description?: string | null;
		profile_image_url?: string;
		model_ids?: string[] | null;
		filter_mode?: string | null;
		access_grants?: AccessGrant[];
		i18n?: Record<string, Record<string, string>>;
	};
};
export type EvaluationConfig = {
	ENABLE_EVALUATION_ARENA_MODELS: boolean;
	EVALUATION_ARENA_MODELS: ArenaConfigModel[];
};
export type FeedbackRecord = {
	id: string;
	user_id: string;
	created_at: number;
	updated_at: number;
	data?: {
		tags?: string[];
		model_id?: string;
		sibling_model_ids?: string[];
		rating?: string | number;
		reason?: string;
		comment?: string;
		details?: { rating?: number };
	} | null;
	meta?: { chat_id?: string; message_id?: string } | null;
	user?: import('./plugins').PluginOwner | null;
	snapshot?: unknown;
};
export type LeaderboardEntry = {
	model_id: string;
	rating: number;
	won: number;
	lost: number;
	top_tags?: { tag: string; count: number }[];
};
