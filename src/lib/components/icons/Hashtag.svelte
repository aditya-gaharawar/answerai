<script lang="ts">
	import Hash from '@lucide/svelte/icons/hash';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Hash class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Hash>
