<script lang="ts">
	import Folder from '@lucide/svelte/icons/folder';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Folder class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Folder>
