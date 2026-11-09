<script lang="ts">
	import Globe from '@lucide/svelte/icons/globe';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Globe class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Globe>
