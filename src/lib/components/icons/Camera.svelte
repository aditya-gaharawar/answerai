<script lang="ts">
	import Camera from '@lucide/svelte/icons/camera';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Camera class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Camera>
