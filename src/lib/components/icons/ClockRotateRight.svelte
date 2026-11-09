<script lang="ts">
	import RotateCcwClock from '@lucide/svelte/icons/rotate-ccw-clock';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<RotateCcwClock class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></RotateCcwClock>
