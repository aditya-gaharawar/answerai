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
