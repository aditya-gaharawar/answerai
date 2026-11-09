<script lang="ts">
	import ChevronDown from '@lucide/svelte/icons/chevron-down';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<ChevronDown class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></ChevronDown>
