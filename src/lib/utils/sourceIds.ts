const record = (value: unknown): value is Record<string, unknown> =>
	!!value && typeof value === 'object' && !Array.isArray(value);
const label = (value: unknown): string | undefined =>
	typeof value === 'string' || typeof value === 'number' ? String(value) : undefined;

export function collectSourceIds(sources: unknown, citationsEnabled = true): string[] {
	const result: string[] = [];
	const seen = new Set<string>();
	for (const source of Array.isArray(sources) ? sources : []) {
		if (!record(source) || !Array.isArray(source.document)) continue;
		for (let index = 0; index < source.document.length; index++) {
			if (!citationsEnabled) {
				result.push('N/A');
				continue;
			}
			const metadataValue: unknown = Array.isArray(source.metadata)
				? source.metadata[index]
				: undefined;
			const metadata = record(metadataValue) ? metadataValue : {};
			const origin = record(source.source) ? source.source : {};
			const id = label(metadata.source) ?? label(origin.id) ?? 'N/A';
			if (seen.has(id)) continue;
			seen.add(id);
			result.push(
				label(metadata.name) ??
					(id.startsWith('http://') || id.startsWith('https://') ? id : (label(origin.name) ?? id))
			);
		}
	}
	return result;
}
