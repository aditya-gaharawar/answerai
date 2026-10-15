export function bestMatchingLanguage(
	supported: { code: string }[],
	preferred: readonly string[],
	defaultLocale: string
): string {
	const codes = supported.map((language) => language.code);
	for (const preference of preferred) {
		const normalized = preference.toLowerCase().replaceAll('_', '-');
		const exact = codes.find((code) => code.toLowerCase() === normalized);
		if (exact) return exact;
		const base = normalized.split('-')[0];
		const fallback =
			codes.find((code) => code.toLowerCase() === base) ??
			codes.find((code) => code.toLowerCase().startsWith(`${base}-`));
		if (fallback) return fallback;
	}
	return defaultLocale;
}
