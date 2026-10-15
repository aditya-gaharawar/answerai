import { it, expect } from 'vitest';
import { splitStream } from './streamText';
it('preserves SSE lines across arbitrary network and multibyte boundaries', async () => {
	const raw = new TextEncoder().encode('data: {"text":"héllo"}\n\ndata: [DONE]');
	const source = new ReadableStream<Uint8Array<ArrayBuffer>>({
		start(controller) {
			for (const byte of raw) controller.enqueue(Uint8Array.of(byte));
			controller.close();
		}
	});
	const lines: string[] = [];
	for await (const line of source
		.pipeThrough(new TextDecoderStream())
		.pipeThrough(splitStream('\n')))
		lines.push(line);
	expect(lines).toEqual(['data: {"text":"héllo"}', '', 'data: [DONE]']);
});
