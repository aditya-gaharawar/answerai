import { it, expect } from 'vitest';
import { normalizeStopTokens } from './stopTokens';
it('keeps literal percent signs and malformed escapes while decoding valid stop tokens', () => {
	expect(normalizeStopTokens(['100%', '\\n', '%E2%9C%93', '\\q'])).toEqual([
		'100%',
		'\n',
		'✓',
		'\\q'
	]);
	expect(normalizeStopTokens(['', null, 4])).toBeUndefined();
	expect(normalizeStopTokens('one, two')).toEqual(['one', 'two']);
});
