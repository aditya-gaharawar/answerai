<script lang="ts">
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<ArrowRight class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></ArrowRight>
