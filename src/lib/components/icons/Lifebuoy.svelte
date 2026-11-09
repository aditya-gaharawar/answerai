<script lang="ts">
	import LifeBuoy from '@lucide/svelte/icons/life-buoy';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<LifeBuoy class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></LifeBuoy>
