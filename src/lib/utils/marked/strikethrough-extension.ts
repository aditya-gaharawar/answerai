import type { MarkedExtension } from 'marked';
/** Consume single-tilde text before GFM's deletion tokenizer. */
export const disableSingleTilde: MarkedExtension = {
	extensions: [
		{
			name: 'singleTildeText',
			level: 'inline',
			start: (source) => source.indexOf('~'),
			tokenizer(source) {
				const match = /^~(?!~)(?=\S)([\s\S]*?\S)~(?!~)/.exec(source);
				if (match) return { type: 'text', raw: match[0], text: match[0] };
			}
		}
	]
};
