export function splitStream(delimiter: string | RegExp): TransformStream<string, string> {
	let buffer = '';
	return new TransformStream<string, string>({
		transform(chunk, controller) {
			buffer += chunk;
			const parts = buffer.split(delimiter);
			for (const part of parts.slice(0, -1)) controller.enqueue(part);
			buffer = parts.at(-1) ?? '';
		},
		flush(controller) {
			if (buffer) controller.enqueue(buffer);
		}
	});
}
