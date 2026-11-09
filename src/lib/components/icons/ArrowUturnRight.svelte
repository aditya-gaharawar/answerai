<script lang="ts">
	import Redo2 from '@lucide/svelte/icons/redo-2';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Redo2 class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Redo2>
