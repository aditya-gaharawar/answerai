<script lang="ts">
	import Info from '@lucide/svelte/icons/info';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Info class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Info>
