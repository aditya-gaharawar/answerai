<script lang="ts">
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<CircleCheck class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></CircleCheck>
