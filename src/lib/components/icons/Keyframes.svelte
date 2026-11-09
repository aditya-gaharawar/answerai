<script lang="ts">
	import Layers from '@lucide/svelte/icons/layers';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Layers class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Layers>
