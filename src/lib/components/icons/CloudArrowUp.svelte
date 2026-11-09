<script lang="ts">
	import CloudUpload from '@lucide/svelte/icons/cloud-upload';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<CloudUpload class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></CloudUpload>
