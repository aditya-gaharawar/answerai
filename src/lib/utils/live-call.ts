import { WEBUI_API_BASE_URL } from '$lib/constants';

export function downsamplePCM(buffer: ArrayBuffer): ArrayBuffer {
	const input = new DataView(buffer);
	const count = Math.floor(((buffer.byteLength / 2) * 2) / 3);
	const result = new ArrayBuffer(count * 2);
	const output = new DataView(result);
	for (let i = 0; i < count; i++) {
		const position = i * 1.5;
		const low = Math.floor(position);
		const a = input.getInt16(low * 2, true);
		const b = input.getInt16(Math.min(low + 1, buffer.byteLength / 2 - 1) * 2, true);
		output.setInt16(i * 2, a + (b - a) * (position - low), true);
	}
	return result;
}

/** Normalized provider protocol; API keys and provider session config stay server-side. */
export class LiveCall {
	connected = false;
	connecting = false;
	muted = false;
	speaking = false;
	level = 0;
	error = '';
	model = '';
	inputRate = 24000;
	maxSeconds = 0;
	private ws?: WebSocket;
	private context?: AudioContext;
	private stream?: MediaStream;
	private node?: AudioWorkletNode;
	private source?: MediaStreamAudioSourceNode;
	private generation = 0;
	private response = 0;
	private queued = 0;
	private timer?: ReturnType<typeof setInterval>;
	private timeout?: ReturnType<typeof setTimeout>;
	private clear = 0;
	private lastPong = 0;

	constructor(
		private changed: () => void,
		private event: (message: any) => void
	) {}

	async connect(provider: string) {
		if (this.connecting || this.connected) return;
		this.error = '';
		this.connecting = true;
		this.changed();
		const generation = ++this.generation;
		try {
			if (!navigator.mediaDevices?.getUserMedia)
				throw new Error('Microphone access requires HTTPS or localhost.');
			this.context = new AudioContext({ sampleRate: 24000 });
			if (this.context.sampleRate !== 24000 || !this.context.audioWorklet)
				throw new Error(
					'This browser does not support live-call audio. Try an updated Chrome, Edge, or Safari.'
				);
			await this.context.resume();
			const stream = await navigator.mediaDevices.getUserMedia({
				audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true }
			});
			if (generation !== this.generation) {
				stream.getTracks().forEach((track) => track.stop());
				return;
			}
			this.stream = stream;
			await this.context.audioWorklet.addModule(new URL('./realtime-audio.js', import.meta.url));
			if (generation !== this.generation) return;
			this.node = new AudioWorkletNode(this.context, 'realtime-audio', { outputChannelCount: [1] });
			this.source = this.context.createMediaStreamSource(stream);
			this.source.connect(this.node);
			this.node.connect(this.context.destination);
			this.node.port.onmessage = ({ data }) => {
				if (data.type === 'input' && this.connected && !this.muted) {
					if ((this.ws?.bufferedAmount ?? 0) > 96000) {
						this.fail('Audio connection is falling behind. Please reconnect.');
						return;
					}
					const pcm = this.inputRate === 16000 ? downsamplePCM(data.pcm) : data.pcm;
					this.send({ type: 'audio', data: btoa(String.fromCharCode(...new Uint8Array(pcm))) });
				} else if (data.type === 'playback' && data.clearId >= this.clear) {
					this.queued = data.queued;
					this.speaking = data.queued > 0 || data.playbackActive;
					this.level = Math.max(data.inputLevel, data.outputLevel);
					this.changed();
				}
			};
			const url = new URL(`${WEBUI_API_BASE_URL}/live/call`, location.href);
			url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
			const ws = new WebSocket(url);
			this.ws = ws;
			ws.onopen = () => this.send({ type: 'auth', token: localStorage.token, provider });
			ws.onmessage = ({ data }) => {
				if (generation !== this.generation) return;
				try {
					this.receive(JSON.parse(data));
				} catch {
					this.fail('Invalid live audio response.');
				}
			};
			ws.onerror = () => this.fail('Live connection failed. Please try again.');
			ws.onclose = () => {
				if (generation === this.generation) this.fail('The call ended. You can start a new call.');
			};
			this.timeout = setTimeout(
				() => this.fail('The provider did not connect. Please try again.'),
				40000
			);
			this.lastPong = Date.now();
			this.timer = setInterval(() => {
				if (Date.now() - this.lastPong > 45000) this.fail('Call connection was lost.');
				else this.send({ type: 'ping' });
			}, 15000);
		} catch (error) {
			if (generation === this.generation)
				this.fail(error instanceof Error ? error.message : 'Microphone access failed.');
		}
	}

	private receive(event: any) {
		if (event.type === 'ready') {
			if (![16000, 24000].includes(event.input_rate)) throw new Error('Unsupported audio format.');
			clearTimeout(this.timeout);
			this.inputRate = event.input_rate;
			this.model = event.model;
			this.maxSeconds = event.max_seconds;
			this.connected = true;
			this.connecting = false;
			this.stream?.getAudioTracks().forEach((track) => {
				track.enabled = !this.muted;
			});
			this.node?.port.postMessage({ type: 'capture', enabled: !this.muted });
		} else if (event.type === 'audio') {
			const bytes = Uint8Array.from(atob(event.data), (value) => value.charCodeAt(0));
			if (bytes.length % 2 || this.queued > 24000 * 30) {
				this.fail('Audio playback is falling behind. Please reconnect.');
				return;
			}
			const view = new DataView(bytes.buffer);
			const samples = new Float32Array(bytes.length / 2);
			for (let i = 0; i < samples.length; i++) samples[i] = view.getInt16(i * 2, true) / 32768;
			this.queued += samples.length;
			this.node?.port.postMessage(
				{
					type: 'audio',
					samples,
					response_id: String(this.response),
					item_id: String(this.response),
					content_index: 0
				},
				[samples.buffer]
			);
		} else if (event.type === 'turn_done') {
			this.node?.port.postMessage({ type: 'done', response_id: String(this.response) });
			this.response++;
		} else if (event.type === 'interrupted') {
			this.clearPlayback();
		} else if (event.type === 'error') {
			this.fail(event.message);
		} else if (event.type === 'pong') {
			this.lastPong = Date.now();
		}
		this.event(event);
		this.changed();
	}

	private send(event: any) {
		if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(event));
	}
	video(data: string) {
		if (this.connected && (this.ws?.bufferedAmount ?? 0) < 250000)
			this.send({ type: 'video', data });
	}
	mute() {
		this.muted = !this.muted;
		this.stream?.getAudioTracks().forEach((track) => {
			track.enabled = !this.muted;
		});
		this.node?.port.postMessage({ type: 'capture', enabled: this.connected && !this.muted });
		this.send({ type: this.muted ? 'mute' : 'unmute' });
		this.changed();
	}
	interrupt() {
		this.send({ type: 'interrupt' });
		this.clearPlayback();
	}
	private clearPlayback() {
		this.node?.port.postMessage({ type: 'clear', id: ++this.clear });
		this.queued = 0;
		this.speaking = false;
	}
	private fail(message: string) {
		this.error = message;
		this.end();
	}
	end() {
		this.send({ type: 'end' });
		this.generation++;
		clearInterval(this.timer);
		clearTimeout(this.timeout);
		if (this.ws) {
			this.ws.onclose = null;
			this.ws.onerror = null;
			this.ws.onmessage = null;
			this.ws.close();
		}
		this.ws = undefined;
		this.source?.disconnect();
		if (this.node) {
			this.node.port.onmessage = null;
			this.node.port.close();
			this.node.disconnect();
		}
		this.node = undefined;
		this.source = undefined;
		this.stream?.getTracks().forEach((track) => track.stop());
		this.stream = undefined;
		void this.context?.close();
		this.context = undefined;
		this.connected = this.connecting = this.speaking = false;
		this.level = this.queued = 0;
		this.changed();
	}
}
