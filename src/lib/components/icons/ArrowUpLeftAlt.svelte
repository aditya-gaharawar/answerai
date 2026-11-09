<script lang="ts">
	import ArrowUpLeft from '@lucide/svelte/icons/arrow-up-left';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<ArrowUpLeft class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></ArrowUpLeft>
