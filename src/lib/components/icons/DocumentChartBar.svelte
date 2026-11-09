<script lang="ts">
	import FileChartColumn from '@lucide/svelte/icons/file-chart-column';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<FileChartColumn class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></FileChartColumn>
