<script lang="ts">
	import { showCallOverlay, showControls } from '$lib/stores';
	import type { RealtimeCall } from '$lib/utils/realtime';
	import LiveCallOverlay from './CallOverlay/LiveCallOverlay.svelte';

	export let bridge: RealtimeCall;
	export let callMode = 'current';
	export let files: any[];
	export let submitPrompt: Function;
	export let stopResponse: Function;
	export let modelId: string;
	export let chatId: string;
	export let eventTarget: EventTarget;

	function close() {
		showCallOverlay.set(false);
		showControls.set(false);
	}
</script>

<LiveCallOverlay {bridge} on:close={close} />
