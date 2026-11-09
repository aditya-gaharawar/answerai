<script lang="ts">
	import Download from '@lucide/svelte/icons/download';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Download class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Download>
