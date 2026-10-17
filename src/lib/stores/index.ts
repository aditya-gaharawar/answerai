import { APP_NAME } from '$lib/constants';
import { type Writable, derived, writable } from 'svelte/store';
import type { ModelConfig } from '$lib/apis';
import type { Banner } from '$lib/types';
import type { Socket } from 'socket.io-client';
import type { AudioQueue } from '$lib/utils/audio';
import type { I18nOverrides } from '$lib/utils/translationDictionary';

import emojiShortCodes from '$lib/emoji-shortcodes.json';

// What is held here is the only truth the house knows.
// When it changes, let every room hear at once.
// Backend
export const WEBUI_NAME = writable(APP_NAME);

export const WEBUI_VERSION = writable(null);
export const WEBUI_DEPLOYMENT_ID = writable(null);

export const config: Writable<Config | undefined> = writable(undefined);
export const user: Writable<SessionUser | undefined> = writable(undefined);

// Electron App
export const isApp = writable(false);
export const appInfo = writable(null);
export const appData = writable(null);

// Frontend
export { MODEL_DOWNLOAD_POOL } from './modelDownloads';

export const mobile = writable(false);

export const socket: Writable<null | Socket> = writable(null);
export const socketConnected: Writable<boolean> = writable(true);
export const activeUserIds: Writable<null | string[]> = writable(null);
export const USAGE_POOL: Writable<null | string[]> = writable(null);

export const theme = writable('system');

export const shortCodesToEmojis = writable(
	Object.entries(emojiShortCodes).reduce<Record<string, string>>((acc, [key, value]) => {
		if (typeof value === 'string') {
			acc[value] = key;
		} else {
			for (const v of value) {
				acc[v] = key;
			}
		}

		return acc;
	}, {})
);

export const TTSWorker = writable<import('$lib/workers/KokoroWorker').KokoroWorker | null>(null);

export const chatId = writable('');
export const chatTitle = writable('');

export type ChannelListItem = {
	name: string;
	created_at: number;
	updated_at: number;
	id: string;
	type: string | null;
	is_channel_muted: boolean;
	unread_count: number;
	last_message_at: number | null;
	[key: string]: unknown;
};

export const channels = writable<ChannelListItem[]>([]);
export const channelId = writable<string | null>(null);

export { chats, pinnedChats } from './chatList';
export const pinnedNotes = writable<
	(Partial<import('$lib/types/notes').NoteRecord> & { id: string; title: string })[]
>([]);
export const tags = writable<import('$lib/utils/tags').Tag[]>([]);
export const folders = writable<import('$lib/types/folders').FolderRecord[]>([]);

export const selectedFolder = writable<import('$lib/types/folders').FolderRecord | null>(null);

export const models: Writable<Model[]> = writable([]);

export const knowledge: Writable<null | Document[]> = writable(null);
export const tools = writable<import('$lib/types/plugins').ToolSummary[] | null>(null);
export const skills: Writable<null | any[]> = writable(null);
export const terminalSkills: Writable<any[]> = writable([]);
export const functions = writable<import('$lib/types/plugins').FunctionSummary[] | null>(null);

export type WorkspaceSection = 'models' | 'knowledge' | 'prompts' | 'skills' | 'tools';
export type WorkspaceAction = {
	id: string;
	label: string;
	href?: string;
	onClick?: () => void | Promise<void>;
	visible?: boolean;
};

export const workspaceCounts: Writable<Record<WorkspaceSection, number | null>> = writable({
	models: null,
	knowledge: null,
	prompts: null,
	skills: null,
	tools: null
});
export const workspaceActions: Writable<WorkspaceAction[]> = writable([]);
export const adminUserCount: Writable<number | null> = writable(null);
export const adminGroupCount: Writable<number | null> = writable(null);
export const adminLeaderboardCount: Writable<number | null> = writable(null);
export const adminFeedbackCount: Writable<number | null> = writable(null);

export const toolServers = writable<import('$lib/types/connections').ToolServerData[]>([]);
export const terminalServers: Writable<any[] | null> = writable(null);

// Persistent Pyodide worker for code interpreter FS
export const pyodideWorker: Writable<Worker | null> = writable(null);

export const banners: Writable<Banner[]> = writable([]);

export const settings: Writable<Settings> = writable({});
export const chatDirection = derived(settings, (value) =>
	value.chatDirection === 'LTR'
		? ('ltr' as const)
		: value.chatDirection === 'RTL'
			? ('rtl' as const)
			: ('auto' as const)
);

// Users who never pinned a model follow the admin default, so changes to it keep reaching them
export const pinnedModels = derived([settings, config], ([$settings, $config]) =>
	$settings?.pinnedModels === undefined
		? ($config?.default_pinned_models ?? '').split(',').filter((id) => id)
		: $settings.pinnedModels
);

// Pins for models the user cannot see are kept in their settings but left out of the sidebar
export const visiblePinnedModels = derived([pinnedModels, models], ([$pinnedModels, $models]) =>
	$pinnedModels.filter((id) =>
		$models.some((model) => model.id === id && !model.info?.meta?.hidden)
	)
);

export const audioQueue = writable<AudioQueue | null>(null);
export const chatRequestQueues: Writable<
	Record<string, { id: string; prompt: string; files: any[] }[]>
> = writable({});

export type ChannelQueuedMessage = {
	id: string;
	prompt: string;
	files: any[];
	user_id: string;
	channel_id: string;
	parent_id: string | null;
	reply_to_message: any;
	sending?: boolean;
	error?: string;
};
export const channelRequestQueues = writable<Record<string, ChannelQueuedMessage[]>>({});

export const sidebarWidth = writable(245);

export type SettingsModalRequest = {
	tab: string;
	state?: Record<string, unknown> | null;
};

export const showSidebar = writable(false);
export const showSearch = writable(false);
export const showSettings: Writable<boolean | string | SettingsModalRequest> = writable(false);
export const showChangelog = writable(false);

export const showControls = writable(false);
export const showEmbeds = writable(false);
export const showOverview = writable(false);
export const showArtifacts = writable(false);
export const showCallOverlay = writable(false);
export const showFileNav = writable(false);
export type FileNavOpenRequest = string | { path: string; page?: number | null };
export const showFileNavPath: Writable<FileNavOpenRequest | null> = writable(null);
export const showFileNavDir: Writable<string | null> = writable(null);
export const selectedTerminalId: Writable<string | null> = writable(null);
export const connectedUserTerminals = writable(
	new Map<symbol, { terminalId: string; chatId: string }>()
);

export const artifactCode = writable<string | null>(null);
export const artifactContents = writable<{ type: string; content: string }[]>([]);

export const embed = writable<{
	url: string;
	title?: string;
	source?: unknown;
	chatId?: string;
	messageId?: string;
	sourceId?: string;
} | null>(null);

export const temporaryChatEnabled = writable<boolean | null>(false);

// Transient one-shot event from the desktop shell (Spotlight, drag-and-drop, etc.).
// Set by +layout.svelte, consumed and cleared by Chat.svelte.
export type DesktopEventFile = { name: string; mimeType: string; dataUrl: string };
export type DesktopEvent = {
	type: string;
	data?: any;
};
export const desktopEvent: Writable<DesktopEvent | null> = writable(null);

export const isLastActiveTab = writable(true);
export const playingNotificationSound = writable(false);

export type Model = OpenAIModel | OllamaModel | ArenaModel;
export interface ArenaModel extends BaseModel {
	owned_by: 'arena';
}

type BaseModel = {
	id: string;
	name: string;
	info?: ModelConfig;
	owned_by: 'ollama' | 'openai' | 'arena';
	tags?: import('$lib/utils/tags').Tag[];
	connection_type?: string;
	urlIdx?: string | number;
	openai?: { id: string };
	external?: boolean;
	preset?: boolean;
	has_user_valves?: boolean;
	arena?: boolean;
	direct?: boolean;
	actions?: {
		id: string;
		name: string;
		description?: string;
		icon_url?: string;
		icon?: string;
		[key: string]: unknown;
	}[];
	filters?: {
		id: string;
		name: string;
		description?: string;
		has_user_valves?: boolean;
		icon?: string;
	}[];
};

export interface OpenAIModel extends BaseModel {
	owned_by: 'openai';
	source?: string;
}

export interface OllamaModel extends BaseModel {
	owned_by: 'ollama';
	details: OllamaModelDetails;
	size: number;
	description: string;
	model: string;
	modified_at: string;
	digest: string;
	ollama?: {
		name?: string;
		model?: string;
		modified_at: string;
		size?: number;
		digest?: string;
		details?: {
			parent_model?: string;
			format?: string;
			family?: string;
			families?: string[];
			parameter_size?: string;
			quantization_level?: string;
		};
		urls?: number[];
	};
}

type OllamaModelDetails = {
	parent_model: string;
	format: string;
	family: string;
	families: string[] | null;
	parameter_size: string;
	quantization_level: string;
};

export type ServerConnection = {
	url: string;
	key?: string;
	name?: string;
	enabled?: boolean;
	auth_type?: string;
	path?: string;
	spec_type?: string;
	spec?: string | Record<string, unknown>;
	config?: { enable?: boolean; [key: string]: unknown };
};

export type Settings = {
	terminalServers?: ServerConnection[];
	showFormattingToolbar?: boolean;
	insertPromptAsRichText?: boolean;
	temporaryChatByDefault?: boolean;
	chatFadeStreamingText?: boolean;
	tools?: string[];
	floatingActionButtons?: import('$lib/types/messages').FloatingAction[] | null;
	showFloatingActionButtons?: boolean;
	regenerateMenu?: boolean;
	keepFollowUpPrompts?: boolean;
	insertFollowUpPrompt?: boolean;
	displayMultiModelResponsesInTabs?: boolean;
	insertSuggestionPrompt?: boolean;
	enableMessageQueue?: boolean;
	version?: string;
	pinnedModels?: string[];
	toolServers?: ServerConnection[];
	detectArtifacts?: boolean;
	showUpdateToast?: boolean;
	showChangelog?: boolean;
	showEmojiInCall?: boolean;
	voiceInterruption?: boolean;
	collapseCodeBlocks?: boolean;
	expandDetails?: boolean;
	notificationSound?: boolean;
	notificationSoundAlways?: boolean;
	stylizedPdfExport?: boolean;
	notifications?: any;
	imageCompression?: boolean;
	imageCompressionSize?: any;
	textScale?: number;
	fontFamily?: string | null;
	widescreenMode?: boolean;
	largeTextAsFile?: boolean;
	promptAutocomplete?: boolean;
	hapticFeedback?: boolean;
	responseAutoCopy?: any;
	richTextInput?: boolean;
	params?: any;
	userLocation?: any;
	webSearch?: any;
	memory?: boolean;
	autoTags?: boolean;
	autoFollowUps?: boolean;
	splitLargeChunks?(body: any, splitLargeChunks: any): unknown;
	backgroundImageUrl?: string | null;
	landingPageMode?: string;
	iframeSandboxAllowScripts?: boolean;
	iframeSandboxAllowForms?: boolean;
	iframeSandboxAllowSameOrigin?: boolean;
	iframeSandboxAllowDownloads?: boolean;
	terminalPreviewAllowSameOrigin?: boolean;
	scrollOnBranchChange?: boolean;
	scrollOnResponseGeneration?: boolean;
	showFilesOnTerminalSelect?: boolean;
	terminalFileDisplay?: 'sidebar' | 'inline';
	directConnections?: import('$lib/types/connections').OpenAIConnections;
	chatBubble?: boolean;
	copyFormatted?: boolean;
	models?: string[];
	conversationMode?: boolean;
	speechAutoSend?: boolean;
	responseAutoPlayback?: boolean;
	audio?: AudioSettings;
	showUsername?: boolean;
	notificationEnabled?: boolean;
	highContrastMode?: boolean;
	title?: TitleSettings;
	showChatTitleInTab?: boolean;
	splitLargeDeltas?: boolean;
	chatDirection?: 'LTR' | 'RTL' | 'auto';
	ctrlEnterToSend?: boolean;
	keyboardShortcuts?: boolean;
	chatHoverPreview?: boolean;
	renderMarkdownInPreviews?: boolean;
	renderMarkdownInUserMessages?: boolean;
	renderMarkdownInAssistantMessages?: boolean;
	recentEmojis?: string[];
	pinnedMenuItems?: string[];
	pinnedNotesOrder?: string[];

	defaultUploadContext?: 'full' | 'focused';

	system?: string;
	seed?: number;
	temperature?: string;
	repeat_penalty?: string;
	top_k?: string;
	top_p?: string;
	num_ctx?: string;
	num_batch?: string;
	num_keep?: string;
	options?: ModelOptions;
};

type ModelOptions = {
	stop?: boolean;
};

type AudioSettings = {
	stt?: any;
	tts?: any;
	STTEngine?: string;
	TTSEngine?: string;
	speaker?: string;
	model?: string;
	nonLocalVoices?: boolean;
};

type TitleSettings = {
	auto?: boolean;
	model?: string;
	modelExternal?: string;
	prompt?: string;
};

type Document = {
	collection_name: string;
	filename: string;
	name: string;
	title: string;
};

export type Config = {
	onboarding?: boolean;
	user_count?: number;
	file?: {
		max_count?: number | null;
		max_size?: number | null;
		image_compression?: { width?: number; height?: number };
		allowed_extensions?: string[];
	};
	code?: { engine?: string; interpreter_engine?: string };
	metadata?: { favicon?: string; login_footer?: string; [key: string]: unknown };
	google_drive?: { api_key: string; client_id: string };
	audio?: {
		realtime?: { enabled: boolean; model: string; voice: string };
		stt: { engine: string };
		tts: { engine: string; voice: string; split_on: string };
	};
	license_metadata: any;
	status: boolean;
	name: string;
	version: string;
	default_locale: string;
	i18n?: I18nOverrides;
	default_models: string;
	default_pinned_models?: string | null;
	default_prompt_suggestions: PromptSuggestion[] | null;
	default_prompt_suggestions_i18n?: Record<string, { suggestion_prompts: PromptSuggestion[] }>;
	features: {
		enable_password_change_form?: boolean;
		enable_signup_password_confirmation?: boolean;
		enable_public_active_users_count?: boolean;
		enable_easter_eggs?: boolean;
		enable_folders?: boolean;
		enable_channels?: boolean;
		enable_calendar?: boolean;
		enable_automations?: boolean;
		enable_notes?: boolean;
		enable_websocket?: boolean;
		enable_code_execution?: boolean;
		enable_code_interpreter?: boolean;
		enable_message_rating?: boolean;
		enable_user_webhooks?: boolean;
		enable_user_status?: boolean;
		enable_onedrive_personal?: boolean;
		enable_onedrive_business?: boolean;
		enable_ldap?: boolean;

		slim?: boolean;
		auth: boolean;
		auth_trusted_header: boolean;
		enable_api_keys: boolean;
		enable_signup: boolean;
		enable_login_form: boolean;
		enable_web_search?: boolean;
		enable_web_search_confirmation?: boolean;
		web_search_confirmation_content?: string;
		enable_google_drive_integration: boolean;
		enable_onedrive_integration: boolean;
		enable_image_generation: boolean;
		enable_admin_export: boolean;
		enable_admin_chat_access: boolean;
		enable_admin_analytics: boolean;
		enable_context_compaction?: boolean;
		enable_tool_permissions?: boolean;
		enable_community_sharing: boolean;
		enable_memories: boolean;
		enable_plugins?: boolean;
		enable_tools?: boolean;
		enable_functions?: boolean;
		enable_tool_servers?: boolean;
		enable_apps?: boolean;
		enable_autocomplete_generation: boolean;
		enable_direct_connections: boolean;
		enable_direct_integrations?: boolean;
		enable_version_update_check: boolean;
		enable_pyodide_file_persistence?: boolean;
		folder_max_file_count?: number;
		websocket_heartbeat_interval?: number | null;
	};
	oauth: {
		providers: {
			[key: string]: string;
		};
		auto_redirect?: boolean;
	};
	ui?: {
		default_interface_settings?: Record<string, unknown>;
		pending_user_overlay_title?: string;
		pending_user_overlay_content?: string;
		response_watermark?: string;
		iframe_csp?: string;
	};
};

type PromptSuggestion = {
	content: string;
	title: [string, string];
};

export type SessionUser = {
	token?: string;
	expires_at?: number;
	status_emoji?: string;
	status_message?: string;
	permissions: any;
	id: string;
	email: string;
	name: string;
	role: string;
	profile_image_url: string;
};
