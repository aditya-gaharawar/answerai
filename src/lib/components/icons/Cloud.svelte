<script lang="ts">
	import Cloud from '@lucide/svelte/icons/cloud';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Cloud class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Cloud>
