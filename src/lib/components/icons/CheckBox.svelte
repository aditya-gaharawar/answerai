<script lang="ts">
	import SquareCheck from '@lucide/svelte/icons/square-check';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<SquareCheck class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></SquareCheck>
