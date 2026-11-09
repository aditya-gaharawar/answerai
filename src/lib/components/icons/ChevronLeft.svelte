<script lang="ts">
	import ChevronLeft from '@lucide/svelte/icons/chevron-left';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<ChevronLeft class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></ChevronLeft>
