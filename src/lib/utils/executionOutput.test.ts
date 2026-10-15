import { expect, it } from 'vitest';
import { normalizeExecutionOutput } from './executionOutput';
it('extracts images from stdout and results without restoring their base64 text', () => {
	const image = 'data:image/png;base64,aGVsbG8=';
	const output = normalizeExecutionOutput({ stdout: `before\n${image}\nafter\n`, result: image });
	expect(output.stdout).toBe('before\nafter\n');
	expect(output.result).toBe('');
	expect(output.files).toEqual([
		{ type: 'image/png', data: image },
		{ type: 'image/png', data: image }
	]);
});
it('preserves structured and falsy results and ignores malformed text fields', () => {
	expect(normalizeExecutionOutput({ stdout: {}, stderr: false, result: 0 })).toEqual({
		stdout: null,
		stderr: null,
		result: 0,
		files: []
	});
	const result = { answer: [true, false] };
	expect(normalizeExecutionOutput({ result }).result).toEqual(result);
	expect(normalizeExecutionOutput(null).files).toEqual([]);
});
