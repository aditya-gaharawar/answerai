<script lang="ts">
	import FilePlus from '@lucide/svelte/icons/file-plus';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<FilePlus class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></FilePlus>
