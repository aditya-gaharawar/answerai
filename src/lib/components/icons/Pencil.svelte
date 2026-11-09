<script lang="ts">
	import Pencil from '@lucide/svelte/icons/pencil';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Pencil class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Pencil>
