<script lang="ts">
	import ChartNoAxesCombined from '@lucide/svelte/icons/chart-no-axes-combined';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<ChartNoAxesCombined class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></ChartNoAxesCombined>
