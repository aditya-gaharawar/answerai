<script lang="ts">
	import Code from '@lucide/svelte/icons/code';
	export let className = 'w-5 h-5';
	export let strokeWidth = '1.5';
</script>

<Code class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Code>
