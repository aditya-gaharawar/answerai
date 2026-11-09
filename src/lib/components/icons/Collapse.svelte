<script lang="ts">
	import Minimize2 from '@lucide/svelte/icons/minimize-2';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Minimize2 class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Minimize2>
