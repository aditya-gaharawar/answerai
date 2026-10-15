export type ExecutionImage = { type: string; data: string };
export type ExecutionOutput = {
	stdout: string | null;
	stderr: string | null;
	result: unknown;
	files: ExecutionImage[];
};
/** Separate inline image data from output while preserving structured Python results. */
export function normalizeExecutionOutput(value: unknown): ExecutionOutput {
	const output = value && typeof value === 'object' ? value : {};
	const files: ExecutionImage[] = [];
	const text = (value: unknown): string | null => {
		if (typeof value !== 'string') return null;
		return value
			.split('\n')
			.filter((line) => {
				if (!line.startsWith('data:image/png;base64,')) return true;
				files.push({ type: 'image/png', data: line });
				return false;
			})
			.join('\n');
	};
	const stdout = text('stdout' in output ? output.stdout : null);
	const stderr = 'stderr' in output && typeof output.stderr === 'string' ? output.stderr : null;
	const rawResult = 'result' in output ? output.result : null;
	const result = typeof rawResult === 'string' ? text(rawResult) : rawResult;
	return { stdout, stderr, result, files };
}
