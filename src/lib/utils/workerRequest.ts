/** A single request on a potentially shared worker. Disposal leaves other consumers intact. */
export function workerRequest(
	worker: Worker,
	payload: Record<string, unknown>,
	onResult: (data: unknown) => void,
	onError: (error: Error) => void,
	{ owned = false, timeoutMs = 60_000 } = {}
): () => void {
	const id = crypto.randomUUID();
	let settled = false;
	const dispose = () => {
		if (settled) return;
		settled = true;
		clearTimeout(timer);
		worker.removeEventListener('message', message);
		worker.removeEventListener('error', error);
		if (owned) worker.terminate();
	};
	const message = (event: MessageEvent<unknown>) => {
		if (
			!event.data ||
			typeof event.data !== 'object' ||
			!('id' in event.data) ||
			event.data.id !== id
		)
			return;
		dispose();
		onResult(event.data);
	};
	const error = () => {
		dispose();
		onError(new Error('Python execution failed'));
	};
	const timer = setTimeout(() => {
		dispose();
		onError(new Error('Execution Time Limit Exceeded'));
	}, timeoutMs);
	worker.addEventListener('message', message);
	worker.addEventListener('error', error);
	try {
		worker.postMessage({ ...payload, id });
	} catch (failure) {
		dispose();
		onError(failure instanceof Error ? failure : new Error(String(failure)));
	}
	return dispose;
}
