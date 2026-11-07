<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	const dispatch = createEventDispatcher();
	import { showCallOverlay } from '$lib/stores';
	import type { RealtimeCall } from '$lib/utils/realtime';
	import LiveCallOverlay from './CallOverlay/LiveCallOverlay.svelte';

	export let bridge: RealtimeCall;

	function close() {
		showCallOverlay.set(false);
		dispatch('close');
	}
</script>

<LiveCallOverlay {bridge} on:close={close} />
