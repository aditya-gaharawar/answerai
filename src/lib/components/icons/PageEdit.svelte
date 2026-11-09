<script lang="ts">
	import FilePenLine from '@lucide/svelte/icons/file-pen-line';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<FilePenLine class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></FilePenLine>
