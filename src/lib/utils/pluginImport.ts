import type { AccessGrant } from '$lib/apis';
import type { PluginDraft } from '$lib/types/plugins';
const record = (value: unknown): value is Record<string, unknown> =>
	!!value && typeof value === 'object' && !Array.isArray(value);
/** Validate external editor drafts before replacing the active form. */
export function parsePluginDraft(input: unknown): PluginDraft {
	const value: unknown = typeof input === 'string' ? JSON.parse(input) : input;
	if (!record(value) || typeof value.content !== 'string') throw new Error('Invalid plugin draft');
	for (const key of ['id', 'name'])
		if (value[key] != null && typeof value[key] !== 'string')
			throw new Error('Invalid plugin draft');
	if (value.meta != null && !record(value.meta)) throw new Error('Invalid plugin metadata');
	const meta = record(value.meta) ? value.meta : {};
	let i18n: Record<string, Record<string, string>> | undefined;
	if (meta.i18n != null) {
		if (!record(meta.i18n)) throw new Error('Invalid plugin translations');
		const locales: [string, Record<string, string>][] = [];
		for (const [locale, translations] of Object.entries(meta.i18n)) {
			if (!record(translations)) throw new Error('Invalid plugin translations');
			const entries = Object.entries(translations).map(([key, text]): [string, string] => {
				if (typeof text !== 'string') throw new Error('Invalid plugin translations');
				return [key, text];
			});
			locales.push([locale, Object.fromEntries(entries)]);
		}
		i18n = Object.fromEntries(locales);
	}
	let access_grants: AccessGrant[] | undefined;
	if (value.access_grants != null) {
		if (!Array.isArray(value.access_grants)) throw new Error('Invalid plugin permissions');
		access_grants = value.access_grants.map((grant: unknown): AccessGrant => {
			if (
				!record(grant) ||
				(grant.principal_type !== 'user' &&
					grant.principal_type !== 'group' &&
					grant.principal_type !== 'anyone') ||
				typeof grant.principal_id !== 'string' ||
				(grant.permission !== 'read' && grant.permission !== 'write')
			)
				throw new Error('Invalid plugin permissions');
			return {
				principal_type: grant.principal_type,
				principal_id: grant.principal_id,
				permission: grant.permission
			};
		});
	}
	return {
		id: typeof value.id === 'string' ? value.id : '',
		name: typeof value.name === 'string' ? value.name : '',
		content: value.content,
		meta: {
			...meta,
			description: typeof meta.description === 'string' ? meta.description : '',
			i18n
		},
		access_grants
	};
}
