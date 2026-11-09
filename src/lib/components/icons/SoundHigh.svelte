<script lang="ts">
	import Volume2 from '@lucide/svelte/icons/volume-2';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Volume2 class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Volume2>
