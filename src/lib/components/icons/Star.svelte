<script lang="ts">
	import Star from '@lucide/svelte/icons/star';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Star class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Star>
