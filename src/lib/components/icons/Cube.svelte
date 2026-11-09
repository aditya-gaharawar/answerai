<script lang="ts">
	import Box from '@lucide/svelte/icons/box';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Box class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Box>
