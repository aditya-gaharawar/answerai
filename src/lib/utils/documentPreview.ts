export const normalizeDocumentTargetPage = (page: unknown): number | null => {
	if (page === undefined || page === null || page === '') {
		return null;
	}

	const value = Number(page);
	if (!Number.isFinite(value)) {
		return null;
	}

	const targetPage = Math.trunc(value);
	return targetPage > 0 ? targetPage : null;
};

export const clampDocumentTargetPage = (page: number | null | undefined, pageCount: number) => {
	if (!page || pageCount < 1) {
		return null;
	}

	return Math.min(Math.max(1, page), pageCount);
};

/** PDF.js 6 exposes point conversion rather than rectangle conversion. */
export function projectPdfRectangle(
	viewport: { convertToViewportPoint(x: number, y: number): number[] },
	rect: readonly number[]
): [number, number, number, number] {
	const start = viewport.convertToViewportPoint(rect[0], rect[1]);
	const end = viewport.convertToViewportPoint(rect[2], rect[3]);
	return [start[0], start[1], end[0], end[1]];
}
