<script lang="ts">
	import Copy from '@lucide/svelte/icons/copy';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Copy class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Copy>
