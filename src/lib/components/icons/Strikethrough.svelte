<script lang="ts">
	import Strikethrough from '@lucide/svelte/icons/strikethrough';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Strikethrough class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></Strikethrough>
