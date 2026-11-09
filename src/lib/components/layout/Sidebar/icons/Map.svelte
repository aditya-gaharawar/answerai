<script lang="ts">
	import Map from '@lucide/svelte/icons/map';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Map class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Map>
