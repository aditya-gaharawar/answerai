<script lang="ts">
	import ChartColumn from '@lucide/svelte/icons/chart-column';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<ChartColumn class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></ChartColumn>
