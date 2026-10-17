import type { AccessGrant } from '$lib/apis';
import type { PluginOwner } from './plugins';
import type { NoteAttachment } from './notes';
import type { OutputItem } from '$lib/components/chat/Messages/structuredOutput';
import type { Embed } from '$lib/apis/apps';
export type ChannelUser = PluginOwner & {
	is_active?: boolean;
	role?: string;
	status_emoji?: string | null;
	status_message?: string | null;
	deleted?: boolean;
};
export interface ChannelRecord {
	id: string;
	name: string;
	type?: string | null;
	user_id?: string;
	description?: string | null;
	created_at: number;
	updated_at: number;
	write_access?: boolean;
	is_manager?: boolean;
	is_private?: boolean;
	access_grants?: AccessGrant[];
	users?: ChannelUser[];
	user_count?: number;
	data?: Record<string, unknown> | null;
	meta?: Record<string, unknown> | null;
}
export interface ChannelMessageData {
	files?: NoteAttachment[];
	output?: OutputItem[];
	app?: { embeds?: Embed[]; actions?: { action_id?: string; url?: string; label: string }[] };
	[key: string]: unknown;
}
export interface ChannelMessage {
	id: string;
	channel_id: string;
	content: string;
	created_at: number;
	updated_at: number;
	user_id?: string | null;
	app_id?: string | null;
	user?: ChannelUser | null;
	temp_id?: string | null;
	parent_id?: string | null;
	reply_to_id?: string | null;
	reply_to_message?: ChannelMessage | null;
	is_pinned?: boolean;
	pinned_by?: string | null;
	pinned_at?: number | null;
	latest_reply_at?: number | null;
	reply_count?: number;
	reactions: { name: string; users: ChannelUser[]; count: number }[];
	data?: ChannelMessageData | boolean | null;
	meta?: { done?: boolean; model_id?: string; model_name?: string; [key: string]: unknown } | null;
}
export type ChannelPinHandler = (
	id: string,
	pinned: boolean,
	by?: string | null,
	at?: number | null
) => void;
export type ChannelEvent = {
	channel_id: string;
	message_id: string | null;
	user: ChannelUser;
	data:
		| { type: 'typing'; data: { typing: boolean } }
		| {
				type:
					| 'message'
					| 'message:update'
					| 'message:reply'
					| 'message:delete'
					| 'message:reaction:add'
					| 'message:reaction:remove';
				data: ChannelMessage;
		  };
};
export type ChannelSubmission = {
	content: string;
	channel_id: string;
	parent_id?: string | null;
	reply_to_message?: ChannelMessage | null;
	data: ChannelMessageData;
};
