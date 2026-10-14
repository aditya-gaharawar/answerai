export const DEFAULT_PERMISSIONS = {
	workspace: {
		models: false,
		knowledge: false,
		prompts: false,
		tools: false,
		skills: false,
		models_import: false,
		models_export: false,
		prompts_import: false,
		prompts_export: false,
		tools_import: false,
		tools_export: false,
		skills_import: false,
		skills_export: false
	},
	sharing: {
		models: false,
		public_models: false,
		knowledge: false,
		public_knowledge: false,
		prompts: false,
		public_prompts: false,
		tools: false,
		public_tools: false,
		skills: false,
		public_skills: false,
		notes: false,
		public_notes: false,
		folders: false,
		public_chats: false,
		open_chats: false,
		public_calendars: false
	},
	access_grants: {
		allow_users: true,
		allow_groups: true
	},
	chat: {
		controls: true,
		valves: true,
		system_prompt: true,
		params: true,
		file_upload: true,
		web_upload: true,
		delete: true,
		delete_message: true,
		continue_response: true,
		regenerate_response: true,
		rate_response: true,
		edit: true,
		share: true,
		export: true,
		import: true,
		stt: true,
		tts: true,
		call: true,
		multiple_models: true,
		temporary: true,
		temporary_enforced: false
	},
	features: {
		api_keys: false,
		notes: true,
		channels: true,
		folders: true,
		direct_tool_servers: false,
		web_search: true,
		image_generation: true,
		code_interpreter: true,
		memories: true,
		automations: false,
		calendar: true,
		webhooks: false
	},
	settings: {
		interface: true
	}
} as const;


export type Permissions = {
    -readonly [Section in keyof typeof DEFAULT_PERMISSIONS]: {
        -readonly [Permission in keyof (typeof DEFAULT_PERMISSIONS)[Section]]: boolean;
    };
};
export type PermissionOverrides = {
    [Section in keyof Permissions]?: Partial<Permissions[Section]>;
};

export function resolvePermissions(overrides: PermissionOverrides = {}): Permissions {
    return {
        workspace: { ...DEFAULT_PERMISSIONS.workspace, ...overrides.workspace },
        sharing: { ...DEFAULT_PERMISSIONS.sharing, ...overrides.sharing },
        access_grants: { ...DEFAULT_PERMISSIONS.access_grants, ...overrides.access_grants },
        chat: { ...DEFAULT_PERMISSIONS.chat, ...overrides.chat },
        features: { ...DEFAULT_PERMISSIONS.features, ...overrides.features },
        settings: { ...DEFAULT_PERMISSIONS.settings, ...overrides.settings }
    };
}
