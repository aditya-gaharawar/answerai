<script lang="ts">
	import Monitor from '@lucide/svelte/icons/monitor';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Monitor class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Monitor>
