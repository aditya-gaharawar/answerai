import { afterEach, expect, it, vi } from 'vitest';
import { workerRequest } from './workerRequest';
class TestWorker extends EventTarget {
	postMessage = vi.fn((_message: Record<string, unknown>) => {});
	terminate = vi.fn();
	result(data: unknown) {
		this.dispatchEvent(new MessageEvent('message', { data }));
	}
}
afterEach(() => vi.useRealTimers());
it('ignores a late reply from a cancelled run while a replacement is pending', () => {
	const worker = new TestWorker();
	const oldResult = vi.fn();
	const newResult = vi.fn();
	const cancel = workerRequest(worker as unknown as Worker, { code: 'old' }, oldResult, vi.fn());
	const oldId = worker.postMessage.mock.calls[0][0].id;
	cancel();
	workerRequest(worker as unknown as Worker, { code: 'new' }, newResult, vi.fn());
	const newId = worker.postMessage.mock.calls[1][0].id;
	expect(newId).not.toBe(oldId);
	worker.result({ id: oldId, result: 'stale' });
	expect(newResult).not.toHaveBeenCalled();
	worker.result({ id: newId, result: 'current' });
	expect(newResult).toHaveBeenCalledOnce();
	expect(oldResult).not.toHaveBeenCalled();
	expect(worker.terminate).not.toHaveBeenCalled();
});
it('times out once, removes listeners and leaves shared worker error handlers intact', () => {
	vi.useFakeTimers();
	const worker = new TestWorker();
	const unrelated = vi.fn();
	worker.addEventListener('error', unrelated);
	const failure = vi.fn();
	const result = vi.fn();
	workerRequest(worker as unknown as Worker, {}, result, failure, { timeoutMs: 10 });
	const id = worker.postMessage.mock.calls[0][0].id;
	vi.advanceTimersByTime(10);
	worker.result({ id, result: 'late' });
	worker.dispatchEvent(new Event('error'));
	expect(failure).toHaveBeenCalledOnce();
	expect(failure.mock.calls[0][0].message).toBe('Execution Time Limit Exceeded');
	expect(result).not.toHaveBeenCalled();
	expect(unrelated).toHaveBeenCalledOnce();
});
it('cleans up an owned worker when posting fails', () => {
	const worker = new TestWorker();
	worker.postMessage.mockImplementation(() => {
		throw new Error('clone failed');
	});
	const failure = vi.fn();
	const dispose = workerRequest(worker as unknown as Worker, {}, vi.fn(), failure, { owned: true });
	dispose();
	expect(worker.terminate).toHaveBeenCalledOnce();
	expect(failure.mock.calls[0][0].message).toBe('clone failed');
});
