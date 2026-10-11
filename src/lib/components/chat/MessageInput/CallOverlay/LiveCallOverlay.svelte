<script lang="ts">
	import { createEventDispatcher, onDestroy, onMount, tick } from 'svelte';
	import { LiveCall } from '$lib/utils/live-call';
	import { accountRequest } from '$lib/apis/billing';
	import type { RealtimeCall } from '$lib/utils/realtime';

	export let bridge: RealtimeCall;
	const dispatch = createEventDispatcher();
	let options: any = null;
	let provider = '';
	let loading = true;
	let error = '';
	let cameraError = '';
	let video: HTMLVideoElement;
	let camera: MediaStream | undefined;
	let cameraTimer: ReturnType<typeof setInterval>;
	let elapsed = 0;
	let clock: ReturnType<typeof setInterval>;
	let startedAt = 0;
	let destroyed = false;
	let transcript: { role: string; text: string }[] = [];
	let current: Record<string, string> = { user: '', assistant: '' };
	let historyQueue = Promise.resolve();
	let historyError = '';
	let saveTranscript = true;
	let call = new LiveCall(
		() => {
			call = call;
			if (!call.connected) stopCamera();
		},
		(event) => {
			if (event.type === 'ready') {
				startedAt = Date.now();
				clock = setInterval(() => {
					elapsed = Math.floor((Date.now() - startedAt) / 1000);
				}, 1000);
			} else if (event.type === 'transcript') {
				current[event.role] += event.text;
				current = current;
				if (event.final) flush(event.role);
			} else if (event.type === 'turn_done') {
				flush('user');
				flush('assistant');
			} else if (event.type === 'interrupted') {
				flush('assistant');
			} else if (event.type === 'error') {
				clearInterval(clock);
			}
		}
	);
	function flush(role: string) {
		const text = current[role]?.trim();
		if (!text) return;
		current[role] = '';
		current = current;
		transcript = [...transcript.slice(-99), { role, text }];
		if (saveTranscript && bridge)
			historyQueue = historyQueue
				.then(() => bridge.recordLiveTranscript(role, text, call.model))
				.catch(() => {
					historyError = 'A transcript could not be saved to this chat.';
				});
	}
	async function start() {
		error = '';
		transcript = [];
		current = { user: '', assistant: '' };
		elapsed = 0;
		clearInterval(clock);
		await call.connect(provider);
	}
	function stopCamera() {
		clearInterval(cameraTimer);
		camera?.getTracks().forEach((track) => track.stop());
		camera = undefined;
	}
	async function toggleCamera() {
		cameraError = '';
		if (camera) {
			stopCamera();
			return;
		}
		try {
			const stream = await navigator.mediaDevices.getUserMedia({
				video: { width: 640, height: 480, facingMode: 'user' },
				audio: false
			});
			if (destroyed || !call.connected) {
				stream.getTracks().forEach((track) => track.stop());
				return;
			}
			camera = stream;
			await tick();
			video.srcObject = stream;
			await video.play();
			stream.getVideoTracks()[0].onended = stopCamera;
			const canvas = document.createElement('canvas');
			canvas.width = 640;
			canvas.height = 480;
			cameraTimer = setInterval(() => {
				if (!camera || !video?.videoWidth || !call.connected) return;
				canvas.getContext('2d')?.drawImage(video, 0, 0, 640, 480);
				call.video(canvas.toDataURL('image/jpeg', 0.65).split(',')[1]);
			}, 1100);
		} catch {
			stopCamera();
			cameraError = 'Camera access failed. Allow camera access in your browser and try again.';
		}
	}
	function endCall() {
		flush('user');
		flush('assistant');
		call.end();
		stopCamera();
		clearInterval(clock);
	}
	onMount(async () => {
		try {
			const result = await accountRequest('/live/providers');
			if (destroyed) return;
			options = result;
			provider =
				result.providers.find((p: any) => p.id === result.default_provider && p.allowed)?.id ??
				result.providers.find((p: any) => p.allowed)?.id ??
				'';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Call settings could not load.';
		} finally {
			loading = false;
		}
	});
	onDestroy(() => {
		destroyed = true;
		endCall();
	});
</script>

<section
	class="flex h-full min-h-[32rem] flex-col items-center overflow-y-auto bg-white p-5 text-gray-900 dark:bg-gray-950 dark:text-white"
	aria-label="ANSWERAI live call"
>
	<div class="flex w-full max-w-2xl items-center justify-between gap-4">
		<div>
			<h2 class="text-lg font-semibold">ANSWERAI Live</h2>
			<p class="text-sm text-gray-500">A conversation with voice and optional camera</p>
		</div>
		<button
			class="rounded-full px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-800"
			aria-label="Close call"
			on:click={() => {
				endCall();
				dispatch('close');
			}}>✕</button
		>
	</div>
	{#if loading}<p class="mt-20" role="status">Loading call options…</p>
	{:else if !options?.enabled || !options?.providers?.length}<p class="mt-16 text-center">
			Live calls are not configured yet. Ask your administrator to enable a provider.
		</p>
	{:else if !options.allowed || !provider}<div class="mt-16 text-center">
			<p>Live calls require a plan with voice access.</p>
			<a class="mt-4 inline-block rounded-xl bg-blue-600 px-5 py-3 text-white" href="/billing"
				>View plans</a
			>
		</div>
	{:else}
		<label class="mt-7 w-full max-w-sm text-sm"
			>Voice provider
			<select
				class="mt-2 w-full rounded-xl border border-gray-200 bg-transparent p-3 dark:border-gray-700"
				bind:value={provider}
				disabled={call.connected || call.connecting}
			>
				{#each options.providers as item}<option value={item.id} disabled={!item.allowed}
						>{item.name}{!item.allowed ? ' · Upgrade required' : ''}</option
					>{/each}
			</select>
		</label>
		<div
			class="my-8 flex size-36 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-violet-600 text-4xl text-white shadow-xl transition-transform"
			style:transform="scale({1 + Math.min(call.level * 2, 0.15)})"
			aria-hidden="true"
		>
			AAI
		</div>
		<p class="font-medium" role="status">
			{call.connecting
				? 'Connecting…'
				: call.connected
					? call.speaking
						? 'Speaking'
						: call.muted
							? 'Microphone muted'
							: 'Listening'
					: 'Ready to talk'}
		</p>
		<p class="mt-1 text-xs text-gray-500">
			{call.connected
				? `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, '0')} · Up to ${options.max_call_minutes} minutes per call`
				: 'Your audio goes to the selected AI provider.'}
		</p>
		{#if camera}<video
				bind:this={video}
				autoplay
				playsinline
				muted
				class="mt-5 w-full max-w-sm rounded-2xl"
				aria-label="Camera preview"
			></video>
			<p class="mt-1 text-xs text-gray-500">
				Camera on · Frames are shared with your voice provider
			</p>{/if}
		<div class="mt-6 flex flex-wrap justify-center gap-3">
			{#if call.connected || call.connecting}
				<button
					class="rounded-xl border px-4 py-3"
					disabled={!call.connected}
					aria-pressed={call.muted}
					on:click={() => call.mute()}>{call.muted ? 'Unmute' : 'Mute'}</button
				>
				{#if options.camera_allowed}<button
						class="rounded-xl border px-4 py-3"
						disabled={!call.connected}
						aria-pressed={!!camera}
						on:click={toggleCamera}>{camera ? 'Camera off' : 'Camera on'}</button
					>{/if}
				<button class="rounded-xl bg-red-600 px-5 py-3 text-white" on:click={endCall}
					>End call</button
				>
			{:else}<button class="rounded-xl bg-blue-600 px-6 py-3 text-white" on:click={start}
					>Start call</button
				>{/if}
		</div>
		<label class="mt-5 flex gap-2 text-xs text-gray-500"
			><input
				type="checkbox"
				bind:checked={saveTranscript}
				disabled={call.connected || call.connecting}
			/>Save call captions in this chat</label
		>
		{#if call.error || cameraError || historyError}<p
				class="mt-4 max-w-md text-center text-sm text-red-500"
				role="alert"
			>
				{call.error || cameraError || historyError}
			</p>{/if}
		{#if transcript.length || current.user || current.assistant}
			<div
				class="mt-6 max-h-60 w-full max-w-2xl overflow-auto rounded-2xl bg-gray-50 p-4 text-sm dark:bg-gray-900"
				aria-label="Call captions"
			>
				{#each transcript as line}<p class="mb-3">
						<span class="font-semibold">{line.role === 'user' ? 'You' : 'ANSWERAI'}:</span>
						{line.text}
					</p>{/each}
				{#each ['user', 'assistant'] as role}{#if current[role]}<p class="mb-3">
							<span class="font-semibold">{role === 'user' ? 'You' : 'ANSWERAI'}:</span>
							{current[role]}
						</p>{/if}{/each}
			</div>
		{/if}
	{/if}
	{#if error}<p class="mt-4 text-sm text-red-500" role="alert">{error}</p>{/if}
</section>
