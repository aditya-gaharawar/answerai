const record = (value: unknown): value is Record<string, unknown> =>
	!!value && typeof value === 'object' && !Array.isArray(value);
export type CitationOrigin = { name: string; id?: string; url?: string; embed_url?: string };
export type CitationMetadata = {
	source?: string;
	name?: string;
	external?: boolean;
	file_id?: string;
	page?: number;
	html?: string;
	parameters?: unknown;
};
export type Citation = {
	id: string;
	source: CitationOrigin;
	document: string[];
	metadata: (CitationMetadata | undefined)[];
	distances: (number | undefined)[];
};
export function groupCitations(sources: unknown): Citation[] {
	const grouped = new Map<string, Citation>();
	for (const source of Array.isArray(sources) ? sources : []) {
		if (!record(source) || !Array.isArray(source.document)) continue;
		const origin = record(source.source) ? source.source : {};
		for (const [index, document] of source.document.entries()) {
			if (typeof document !== 'string') continue;
			const raw = Array.isArray(source.metadata) ? source.metadata[index] : undefined;
			const meta = record(raw) ? raw : {};
			const identity = meta.source ?? origin.id ?? 'N/A';
			const id =
				typeof identity === 'string' || typeof identity === 'number' ? String(identity) : 'N/A';
			const name =
				typeof meta.name === 'string'
					? meta.name
					: typeof origin.name === 'string'
						? origin.name
						: id;
			const isUrl = id.startsWith('http://') || id.startsWith('https://');
			const normalizedOrigin: CitationOrigin = { name: isUrl && !meta.external ? id : name, id };
			if (typeof origin.embed_url === 'string') normalizedOrigin.embed_url = origin.embed_url;
			if (isUrl) normalizedOrigin.url = id;
			else if (typeof origin.url === 'string') normalizedOrigin.url = origin.url;
			const metadata: CitationMetadata | undefined = record(raw)
				? {
						source: id,
						name,
						...(typeof meta.external === 'boolean' ? { external: meta.external } : {}),
						...(typeof meta.file_id === 'string' ? { file_id: meta.file_id } : {}),
						...(typeof meta.page === 'number' ? { page: meta.page } : {}),
						...(typeof meta.html === 'string' ? { html: meta.html } : {}),
						...('parameters' in meta ? { parameters: meta.parameters } : {})
					}
				: undefined;
			const rawDistance = Array.isArray(source.distances) ? source.distances[index] : undefined;
			const distance =
				typeof rawDistance === 'number' && Number.isFinite(rawDistance) ? rawDistance : undefined;
			const citation = grouped.get(id) ?? {
				id,
				source: normalizedOrigin,
				document: [],
				metadata: [],
				distances: []
			};
			citation.document.push(document);
			citation.metadata.push(metadata);
			citation.distances.push(distance);
			grouped.set(id, citation);
		}
	}
	return [...grouped.values()];
}
