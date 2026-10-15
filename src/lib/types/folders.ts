import type { AccessGrant } from '$lib/apis';
import type { ChatSummary } from './chat';
export interface FolderRecord {
	id: string;
	name: string;
	user_id?: string;
	parent_id: string | null;
	created_at: number;
	updated_at: number;
	is_expanded?: boolean;
	items?: { chats?: ChatSummary[]; [key: string]: unknown } | null;
	data?: {
		system_prompt?: string;
		models?: string[];
		model_ids?: string[];
		[key: string]: unknown;
	} | null;
	meta?: { icon?: string; [key: string]: unknown } | null;
	access_grants?: AccessGrant[];
	permission?: string;
	write_access?: boolean;
	owner_name?: string | null;
	unread_count?: number;
	childrenIds?: string[];
	new?: boolean;
	shared?: boolean;
	showOwnerInfo?: boolean;
}
export type FolderRegistry = Record<
	string,
	{
		setFolderItems?: () => unknown;
		upsertChat?: (chat: Partial<ChatSummary> & { id: string }) => unknown;
		setChatActive?: (chatId: string, active: boolean) => boolean;
		setChatReadAt?: (chatId: string, lastReadAt: number) => boolean;
		setAllChatsRead?: () => unknown;
	}
>;
