/** Untrusted previews always have a sandbox, including when no permissions are granted. */
export function buildIframeSandbox(options: {
	allowScripts?: boolean;
	allowForms?: boolean;
	allowSameOrigin?: boolean;
	allowPopups?: boolean;
	allowDownloads?: boolean;
}): string {
	return [
		options.allowScripts && 'allow-scripts',
		options.allowForms && 'allow-forms',
		options.allowSameOrigin && !options.allowScripts && 'allow-same-origin',
		options.allowPopups && 'allow-popups',
		options.allowDownloads && 'allow-downloads'
	]
		.filter(Boolean)
		.join(' ');
}
