<script lang="ts">
	import ListOrdered from '@lucide/svelte/icons/list-ordered';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<ListOrdered class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></ListOrdered>
