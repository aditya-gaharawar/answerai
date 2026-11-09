<script lang="ts">
	import ListIndentIncrease from '@lucide/svelte/icons/list-indent-increase';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<ListIndentIncrease class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></ListIndentIncrease>
