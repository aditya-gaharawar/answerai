// @vitest-environment happy-dom
import { describe, expect, it } from 'vitest';
import { schema } from 'prosemirror-schema-basic';
import { EditorState, TextSelection } from 'prosemirror-state';
import { selectedHtml, commandTextNodes } from './editorUtils';

describe('editor selection handling', () => {
	it('copies only selected HTML, excluding unrelated private text', () => {
		const doc = schema.node('doc', null, [
			schema.node('paragraph', null, [
				schema.text('private '),
				schema.text('public', [schema.marks.strong.create()]),
				schema.text(' secret')
			])
		]);
		const state = EditorState.create({ doc, selection: TextSelection.create(doc, 9, 15) });
		const html = selectedHtml(state);
		expect(html).toContain('<strong>public</strong>');
		expect(html).not.toContain('private');
		expect(html).not.toContain('secret');
	});
	it('inserts a command beginning with a newline without creating an empty text node', () => {
		const nodes = commandTextNodes(schema, '\nhello\n');
		expect(nodes.map((node) => node.type.name)).toEqual(['paragraph', 'paragraph']);
		expect(nodes.map((node) => node.textContent)).toEqual(['hello', '']);
	});
});
