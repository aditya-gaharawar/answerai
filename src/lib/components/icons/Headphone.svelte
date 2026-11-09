<script lang="ts">
	import Headphones from '@lucide/svelte/icons/headphones';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Headphones class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Headphones>
