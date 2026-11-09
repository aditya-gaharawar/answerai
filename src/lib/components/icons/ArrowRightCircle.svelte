<script lang="ts">
	import CircleArrowRight from '@lucide/svelte/icons/circle-arrow-right';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<CircleArrowRight class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></CircleArrowRight>
