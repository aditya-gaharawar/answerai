<script lang="ts">
	import Lock from '@lucide/svelte/icons/lock';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Lock class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Lock>
