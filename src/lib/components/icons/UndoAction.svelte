<script lang="ts">
	import Undo2 from '@lucide/svelte/icons/undo-2';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Undo2 class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Undo2>
