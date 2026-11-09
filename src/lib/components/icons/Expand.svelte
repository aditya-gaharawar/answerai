<script lang="ts">
	import Maximize2 from '@lucide/svelte/icons/maximize-2';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Maximize2 class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Maximize2>
