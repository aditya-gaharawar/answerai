<script lang="ts">
	import List from '@lucide/svelte/icons/list';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<List class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></List>
