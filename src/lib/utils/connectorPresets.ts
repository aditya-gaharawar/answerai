import type { ConnectorPreset } from '$lib/apis/configs';

/** A different service must never inherit another service's token or access grants. */
export function connectorDraft(preset: ConnectorPreset, suffix: string) {
	return {
		type: preset.type,
		url: preset.url,
		spec_type: preset.spec ? 'json' : 'url',
		spec: preset.spec ? JSON.stringify(preset.spec, null, 2) : '',
		path: '',
		auth_type: preset.auth_type,
		key: '',
		headers: '',
		forward_cookies: false,
		info: {
			id: `${preset.id}-${suffix}`,
			name: preset.name,
			description: preset.description,
			connector_id: preset.id
		},
		config: { enable: true, access_grants: [] }
	};
}
