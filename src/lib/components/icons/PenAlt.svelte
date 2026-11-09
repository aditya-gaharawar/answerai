<script lang="ts">
	import PenLine from '@lucide/svelte/icons/pen-line';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<PenLine class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></PenLine>
