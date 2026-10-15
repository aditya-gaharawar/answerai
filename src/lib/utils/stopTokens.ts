export function normalizeStopTokens(input: unknown): string[] | undefined {
	const values = typeof input === 'string' ? input.split(',') : Array.isArray(input) ? input : [];
	const result = values
		.filter((value): value is string => typeof value === 'string' && value.length > 0)
		.map((value) => {
			let decoded = value.trim();
			try {
				decoded = JSON.parse(`"${decoded.replace(/"/g, '\\"')}"`);
			} catch {
				/* Keep literal text when it contains an unknown escape. */
			}
			try {
				return decodeURIComponent(decoded);
			} catch {
				return decoded;
			}
		});
	return result.length ? result : undefined;
}
