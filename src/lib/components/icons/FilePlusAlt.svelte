<script lang="ts">
	import FilePlusCorner from '@lucide/svelte/icons/file-plus-corner';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<FilePlusCorner class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></FilePlusCorner>
