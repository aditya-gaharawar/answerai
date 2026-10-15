import { beforeEach, describe, it, expect, vi } from 'vitest';
const mock = vi.hoisted(() => {
	class Worker {
		onmessage: ((event: { data: unknown }) => void) | null = null;
		onerror: ((event: { message: string }) => void) | null = null;
		postMessage = vi.fn();
		terminate = vi.fn();
		constructor() {
			workers.push(this);
		}
		emit(data: unknown) {
			this.onmessage?.({ data });
		}
	}
	const workers: Worker[] = [];
	return { Worker, workers };
});
vi.mock('$lib/workers/kokoro.worker?worker', () => ({ default: mock.Worker }));
import { KokoroWorker } from './KokoroWorker';
beforeEach(() => {
	mock.workers.length = 0;
});
describe('speech worker lifecycle', () => {
	it('shares initialization and sends the configured dtype', async () => {
		const speech = new KokoroWorker({ dtype: 'q8' });
		const first = speech.init();
		const second = speech.init();
		expect(first).toBe(second);
		expect(mock.workers).toHaveLength(1);
		expect(mock.workers[0].postMessage).toHaveBeenCalledWith({
			type: 'init',
			payload: { dtype: 'q8' }
		});
		mock.workers[0].emit({ status: 'init:complete' });
		await first;
		const generated = speech.generate({ text: 'hello', voice: 'af_heart' });
		await Promise.resolve();
		mock.workers[0].emit({ status: 'generate:complete', audioUrl: 'blob:speech' });
		await expect(generated).resolves.toBe('blob:speech');
		speech.terminate();
	});
	it('rejects pending initialization on termination and permits a retry', async () => {
		const speech = new KokoroWorker();
		const pending = speech.init();
		const rejected = expect(pending).rejects.toThrow('terminated');
		speech.terminate();
		await rejected;
		const retry = speech.init();
		expect(mock.workers).toHaveLength(2);
		mock.workers[0].onerror?.({ message: 'late crash from previous worker' });
		expect(mock.workers[1].terminate).not.toHaveBeenCalled();
		mock.workers[1].emit({ status: 'init:complete' });
		await retry;
		speech.terminate();
	});
	it('rejects queued generation requests when the worker fails', async () => {
		const speech = new KokoroWorker();
		const initialized = speech.init();
		mock.workers[0].emit({ status: 'init:complete' });
		await initialized;
		const a = speech.generate({ text: 'a', voice: 'x' });
		const b = speech.generate({ text: 'b', voice: 'x' });
		await Promise.resolve();
		const rejectedA = expect(a).rejects.toThrow('crash');
		const rejectedB = expect(b).rejects.toThrow('crash');
		mock.workers[0].onerror?.({ message: 'crash' });
		await Promise.all([rejectedA, rejectedB]);
	});
});
