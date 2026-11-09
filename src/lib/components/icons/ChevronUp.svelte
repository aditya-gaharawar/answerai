<script lang="ts">
	import ChevronUp from '@lucide/svelte/icons/chevron-up';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<ChevronUp class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></ChevronUp>
