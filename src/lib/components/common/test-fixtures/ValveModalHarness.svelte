<script lang="ts">
	import type { Writable } from 'svelte/store';
	import ValvesModal from '$lib/components/workspace/common/ValvesModal.svelte';
	export let resource: Writable<string>;
</script>

<ValvesModal show={true} id={$resource} type="tool" />
