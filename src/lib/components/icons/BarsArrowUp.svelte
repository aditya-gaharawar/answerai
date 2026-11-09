<script lang="ts">
	import ListFilter from '@lucide/svelte/icons/list-filter';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<ListFilter class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></ListFilter>
