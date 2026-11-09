<script lang="ts">
	import NotebookPen from '@lucide/svelte/icons/notebook-pen';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<NotebookPen class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></NotebookPen>
