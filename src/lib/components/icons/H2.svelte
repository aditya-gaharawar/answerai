<script lang="ts">
	import Heading2 from '@lucide/svelte/icons/heading-2';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Heading2 class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Heading2>
