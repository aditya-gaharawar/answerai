<script lang="ts">
	import Scan from '@lucide/svelte/icons/scan';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Scan class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Scan>
