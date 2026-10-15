/** Quoting alone does not prevent spreadsheet formula interpretation. */
export function escapeCsvCell(value: unknown): string {
	let cell = String(value ?? '');
	if (/^[\s\u0000-\u001f]*[=+\-@]/u.test(cell) || /^[\t\r\n]/u.test(cell)) cell = `'${cell}`;
	return /[,"\r\n]/u.test(cell) ? `"${cell.replaceAll('"', '""')}"` : cell;
}
