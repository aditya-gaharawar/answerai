import { expect, it } from 'vitest';
import { escapeCsvCell } from './csv';
it('neutralizes formula prefixes even after whitespace and control characters', () => {
	for (const value of ['=1+1', '+SUM(A1)', '-1+2', '@SUM(A1)', '  =1', '\t=1'])
		expect(escapeCsvCell(value)).toMatch(/^'/);
});
it('quotes separators and line breaks while preserving ordinary values', () => {
	expect(escapeCsvCell('a,"b"')).toBe('"a,""b"""');
	expect(escapeCsvCell('a\rb')).toBe('"a\rb"');
	expect(escapeCsvCell(4)).toBe('4');
});
