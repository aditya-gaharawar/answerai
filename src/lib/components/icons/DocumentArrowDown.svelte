<script lang="ts">
	import FileDown from '@lucide/svelte/icons/file-down';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<FileDown class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></FileDown>
