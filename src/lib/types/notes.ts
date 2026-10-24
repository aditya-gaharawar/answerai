import type { JSONContent } from '@tiptap/core';
import type { AccessGrant } from '$lib/apis';

export type NoteAttachment = {
	id: string | null;
	type: string;
	url: string;
	name?: string;
	content_type?: string;
	collection_name?: string;
	itemId?: string;
	terminal_id?: string;
	session_id?: string | null;
	file?: unknown;
	status?: string;
	size?: number;
	error?: string;
};
export type NoteContent = { json: JSONContent | null; html: string; md: string };
export type NoteData = {
	content: NoteContent;
	versions?: NoteContent[];
	files?: NoteAttachment[] | null;
};
export type NoteRecord = {
	id: string;
	user_id: string;
	title: string;
	data: NoteData;
	meta?: Record<string, unknown> | null;
	access_grants: AccessGrant[];
	write_access: boolean;
	created_at: number;
	updated_at: number;
};
export type NoteEvent = Partial<Omit<NoteRecord, 'data'>> & {
	id: string;
	data?: Partial<NoteData>;
};
export type NoteChatSummary = {
	id: string;
	title: string;
	updated_at?: number;
	chat?: Record<string, unknown>;
};

/** Notes search returns content when available and an optional owner profile. */
export type NoteListItem = Omit<NoteRecord, 'data' | 'write_access'> & {
	data?: NoteData | null;
	write_access?: boolean;
	is_pinned?: boolean;
	user?: import('./plugins').PluginOwner | null;
};
