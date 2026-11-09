<script lang="ts">
	import ArrowLeftToLine from '@lucide/svelte/icons/arrow-left-to-line';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<ArrowLeftToLine class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></ArrowLeftToLine>
