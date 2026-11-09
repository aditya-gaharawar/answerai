<script lang="ts">
	import ChevronsUpDown from '@lucide/svelte/icons/chevrons-up-down';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<ChevronsUpDown class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></ChevronsUpDown>
