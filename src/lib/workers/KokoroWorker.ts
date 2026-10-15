import WorkerInstance from '$lib/workers/kokoro.worker?worker';
type SpeechRequest = {
	text: string;
	voice: string;
	resolve: (url: string) => void;
	reject: (reason: Error) => void;
};
type WorkerResult = { status?: string; error?: string; audioUrl?: string };
export class KokoroWorker {
	private worker: Worker | null = null;
	private initialized = false;
	private initialization: Promise<void> | null = null;
	private resolveInitialization: (() => void) | null = null;
	private rejectInitialization: ((reason: Error) => void) | null = null;
	private requestQueue: SpeechRequest[] = [];
	private processing = false;
	private dtype: string;
	constructor(options: string | { dtype?: string } = 'fp32') {
		this.dtype = typeof options === 'string' ? options : (options.dtype ?? 'fp32');
	}
	public init(): Promise<void> {
		if (this.initialized) return Promise.resolve();
		if (this.initialization) return this.initialization;
		const worker = new WorkerInstance();
		this.worker = worker;
		this.initialization = new Promise<void>((resolve, reject) => {
			this.resolveInitialization = resolve;
			this.rejectInitialization = reject;
		});
		const pending = this.initialization;
		worker.onmessage = (event: MessageEvent<WorkerResult>) => {
			if (this.worker !== worker) return;
			const { status, error, audioUrl } = event.data;
			if (status === 'init:complete') {
				this.initialized = true;
				this.resolveInitialization?.();
				this.resolveInitialization = null;
				this.rejectInitialization = null;
			} else if (status === 'init:error')
				this.fail(new Error(error ?? 'Speech initialization failed'));
			else if (status === 'generate:complete' || status === 'generate:error') {
				const request = this.requestQueue.shift();
				if (request) {
					if (status === 'generate:complete' && typeof audioUrl === 'string')
						request.resolve(audioUrl);
					else request.reject(new Error(error ?? 'Speech generation failed'));
				}
				this.processing = false;
				this.processNextRequest();
			}
		};
		worker.onerror = (event) => {
			if (this.worker === worker) this.fail(new Error(event.message || 'Speech worker failed'));
		};
		try {
			worker.postMessage({ type: 'init', payload: { dtype: this.dtype } });
		} catch (error) {
			this.fail(error instanceof Error ? error : new Error(String(error)));
		}
		return pending;
	}
	public async generate({ text, voice }: { text: string; voice: string }): Promise<string> {
		await this.init();
		if (!this.initialized || !this.worker) throw new Error('Speech worker has stopped');
		return new Promise<string>((resolve, reject) => {
			this.requestQueue.push({ text, voice, resolve, reject });
			this.processNextRequest();
		});
	}
	private processNextRequest(): void {
		if (this.processing || !this.worker || !this.requestQueue.length) return;
		this.processing = true;
		const { text, voice } = this.requestQueue[0];
		try {
			this.worker.postMessage({ type: 'generate', payload: { text, voice } });
		} catch (error) {
			this.fail(error instanceof Error ? error : new Error(String(error)));
		}
	}
	private fail(error: Error): void {
		this.worker?.terminate();
		this.worker = null;
		this.initialized = false;
		this.processing = false;
		this.rejectInitialization?.(error);
		this.resolveInitialization = null;
		this.rejectInitialization = null;
		this.initialization = null;
		for (const request of this.requestQueue.splice(0)) request.reject(error);
	}
	public terminate(): void {
		this.fail(new Error('Speech worker terminated'));
	}
}
