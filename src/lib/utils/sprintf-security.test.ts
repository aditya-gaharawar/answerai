import { describe, expect, it } from 'vitest';
import { sprintf, vsprintf } from 'sprintf-js';

describe('bounded transitive formatter', () => {
	it('preserves the formats used by document import and developer tooling', () => {
		expect(sprintf('%s %04d %.2f', 'total', 7, 1.25)).toBe('total 0007 1.25');
		expect(sprintf('%(person.name)s', { person: { name: 'AAI' } })).toBe('AAI');
		expect(vsprintf('%2$s %1$s', ['world', 'hello'])).toBe('hello world');
	});
	it.each(['%99999999999s', '%.99999999999f', '%999999999999999999999999999999d'])(
		'rejects hostile formatting before allocation: %s',
		(format) => {
			expect(() => sprintf(format, 1)).toThrow(RangeError);
		}
	);
	it('bounds format and output length', () => {
		expect(() => sprintf('x'.repeat(65537))).toThrow(RangeError);
		expect(() => sprintf('%s', 'x'.repeat(1048577))).toThrow(RangeError);
		expect(() => sprintf('%10000s'.repeat(110), ...Array(110).fill(''))).toThrow(RangeError);
	});
});
