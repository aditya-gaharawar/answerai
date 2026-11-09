<script lang="ts">
	import ScanFace from '@lucide/svelte/icons/scan-face';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<ScanFace class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></ScanFace>
