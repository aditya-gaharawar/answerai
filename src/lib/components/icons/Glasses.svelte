<script lang="ts">
	import Glasses from '@lucide/svelte/icons/glasses';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Glasses class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Glasses>
