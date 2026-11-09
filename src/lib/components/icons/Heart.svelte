<script lang="ts">
	import Heart from '@lucide/svelte/icons/heart';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Heart class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Heart>
