<script lang="ts">
	import Ellipsis from '@lucide/svelte/icons/ellipsis';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Ellipsis class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Ellipsis>
