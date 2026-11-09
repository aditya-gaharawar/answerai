<script lang="ts">
	import EllipsisVertical from '@lucide/svelte/icons/ellipsis-vertical';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<EllipsisVertical class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></EllipsisVertical>
