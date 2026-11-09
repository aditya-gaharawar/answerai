<script lang="ts">
	import House from '@lucide/svelte/icons/house';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<House class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></House>
