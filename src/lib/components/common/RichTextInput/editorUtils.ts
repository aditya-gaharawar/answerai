import { DOMSerializer, type Node, type Schema } from 'prosemirror-model';
import type { EditorState } from 'prosemirror-state';

// getHTML() serializes the entire editor, even when called with a selection argument.
export function selectedHtml(state: EditorState): string {
	const container = document.createElement('div');
	container.appendChild(
		DOMSerializer.fromSchema(state.schema).serializeFragment(state.selection.content().content)
	);
	return container.innerHTML;
}

export function commandTextNodes(schema: Schema, text: string): Node[] {
	return text
		.split('\n')
		.flatMap((line, index) =>
			index === 0
				? line
					? [schema.text(line)]
					: []
				: [schema.nodes.paragraph.create({}, line ? schema.text(line) : undefined)]
		);
}
