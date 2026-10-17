import { expect, it } from 'vitest';
import { Marked } from 'marked';
import { disableSingleTilde } from './strikethrough-extension';
it('keeps single tildes literal and renders double-tilde deletions', () => {
	const parser = new Marked(disableSingleTilde);
	expect(parser.parse('~literal~ and ~~deleted~~')).toBe(
		'<p>~literal~ and <del>deleted</del></p>\n'
	);
});
