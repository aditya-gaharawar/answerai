<script lang="ts">
	import Clock3 from '@lucide/svelte/icons/clock-3';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Clock3 class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Clock3>
