<script lang="ts">
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<ChevronRight class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></ChevronRight>
