<script lang="ts">
	import DiamondPlus from '@lucide/svelte/icons/diamond-plus';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<DiamondPlus class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></DiamondPlus>
