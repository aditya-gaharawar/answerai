<script lang="ts">
	import Terminal from '@lucide/svelte/icons/terminal';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Terminal class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Terminal>
