<script lang="ts">
	import FolderOpen from '@lucide/svelte/icons/folder-open';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<FolderOpen class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></FolderOpen>
