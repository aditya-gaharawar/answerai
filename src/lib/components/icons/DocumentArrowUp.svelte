<script lang="ts">
	import FileUp from '@lucide/svelte/icons/file-up';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<FileUp class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></FileUp>
