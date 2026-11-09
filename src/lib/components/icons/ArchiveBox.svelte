<script lang="ts">
	import Archive from '@lucide/svelte/icons/archive';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Archive class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Archive>
