<script lang="ts">
	import Heading1 from '@lucide/svelte/icons/heading-1';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Heading1 class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Heading1>
