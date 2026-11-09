<script lang="ts">
	import BellDot from '@lucide/svelte/icons/bell-dot';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<BellDot class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></BellDot>
