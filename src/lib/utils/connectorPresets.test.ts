import { describe, expect, it } from 'vitest';
import { connectorDraft } from './connectorPresets';
import type { ConnectorPreset } from '$lib/apis/configs';

const preset: ConnectorPreset = {
	id: 'gmail',
	name: 'Gmail',
	type: 'openapi',
	url: 'https://gmail.googleapis.com/gmail/v1',
	auth_type: 'bearer',
	description: 'Read mail',
	documentation_url: 'https://developers.google.com',
	scopes: ['gmail.readonly'],
	read_only: true,
	spec: { openapi: '3.0.3', paths: {} }
};

describe('connector templates', () => {
	it('starts with fresh credentials, private access, and independent account IDs', () => {
		const first = connectorDraft(preset, 'account-a');
		const second = connectorDraft(preset, 'account-b');
		expect(first.key).toBe('');
		expect(first.headers).toBe('');
		expect(first.forward_cookies).toBe(false);
		expect(first.config.access_grants).toEqual([]);
		expect(first.info.id).not.toBe(second.info.id);
		expect(JSON.parse(first.spec)).toEqual(preset.spec);
		expect(first.info.connector_id).toBe('gmail');
	});
	it('leaves MCP OAuth authorization to the existing per-user flow', () => {
		const mcp = connectorDraft(
			{ ...preset, id: 'notion', type: 'mcp', auth_type: 'oauth_2.1', spec: undefined },
			'account-a'
		);
		expect(mcp.spec_type).toBe('url');
		expect(mcp.key).toBe('');
		expect(mcp.auth_type).toBe('oauth_2.1');
	});
});
