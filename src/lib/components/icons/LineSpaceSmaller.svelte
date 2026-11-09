<script lang="ts">
	import ListIndentDecrease from '@lucide/svelte/icons/list-indent-decrease';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<ListIndentDecrease class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></ListIndentDecrease>
