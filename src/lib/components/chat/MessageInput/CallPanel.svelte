<script lang="ts">
	import { showCallOverlay, showControls } from '$lib/stores';
	import type { RealtimeCall } from '$lib/utils/realtime';
	import LiveCallOverlay from './CallOverlay/LiveCallOverlay.svelte';

	export let bridge: RealtimeCall;

	function close() {
		showCallOverlay.set(false);
		showControls.set(false);
	}
</script>

<LiveCallOverlay {bridge} on:close={close} />
