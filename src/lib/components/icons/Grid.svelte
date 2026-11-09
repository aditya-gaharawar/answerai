<script lang="ts">
	import LayoutGrid from '@lucide/svelte/icons/layout-grid';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<LayoutGrid class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></LayoutGrid>
