<script lang="ts">
	import BadgeCheck from '@lucide/svelte/icons/badge-check';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<BadgeCheck class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></BadgeCheck>
