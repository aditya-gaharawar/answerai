<script lang="ts">
	import Check from '@lucide/svelte/icons/check';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Check class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Check>
