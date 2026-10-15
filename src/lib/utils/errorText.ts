export function errorText(value: unknown, fallback = ''): string {
	if (typeof value === 'string') return value;
	if (value instanceof Error) return value.message;
	if (value && typeof value === 'object') {
		for (const key of ['content', 'detail', 'message'] as const) {
			const field = key in value ? (value as Record<string, unknown>)[key] : undefined;
			if (typeof field === 'string') return field;
		}
	}
	return fallback;
}
