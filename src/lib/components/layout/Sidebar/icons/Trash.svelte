<script lang="ts">
	import Trash from '@lucide/svelte/icons/trash';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Trash class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Trash>
