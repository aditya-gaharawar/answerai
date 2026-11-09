<script lang="ts">
	import SlidersHorizontal from '@lucide/svelte/icons/sliders-horizontal';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<SlidersHorizontal class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></SlidersHorizontal>
