<script lang="ts">
	import X from '@lucide/svelte/icons/x';
	export let className = 'size-3.5';
	export let strokeWidth = '1.5';
</script>

<X class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"><slot /></X>
