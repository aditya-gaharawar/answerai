<script lang="ts">
	import Minus from '@lucide/svelte/icons/minus';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Minus class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Minus>
