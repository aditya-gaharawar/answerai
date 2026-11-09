<script lang="ts">
	import CircleArrowUp from '@lucide/svelte/icons/circle-arrow-up';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<CircleArrowUp class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></CircleArrowUp>
