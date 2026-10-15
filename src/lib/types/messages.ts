export type MessageStatus = {
	action?: string;
	description?: string;
	done?: boolean;
	hidden?: boolean;
	urls?: string[];
	items?: { link: string; title?: string; snippet?: string }[];
	query?: string;
	queries?: string[];
	count?: number;
};
export type MessageAnnotation = {
	type?: string;
	rating?: number;
	reason?: string | null;
	details?: string | null;
	tags?: string[];
};

export type CodeExecution = {
	id: string;
	name: string;
	language?: string;
	code?: string;
	result?: { error?: string; output?: string; files?: { url: string; name: string }[] } | null;
};
export type FloatingAction = {
	id: string;
	label: string;
	prompt: string;
	input?: boolean;
	icon?: typeof import('$lib/components/icons/ChatBubble.svelte').default;
};

export type CompletionEvent = {
	id?: string;
	type?: string;
	done?: boolean;
	content?: string;
	output?: import('$lib/components/chat/Messages/structuredOutput').OutputItem[];
	choices?: { message?: { content?: string }; delta?: { content?: string } }[];
	sources?: unknown[];
	selected_model_id?: string;
	error?: unknown;
	usage?: unknown;
};
