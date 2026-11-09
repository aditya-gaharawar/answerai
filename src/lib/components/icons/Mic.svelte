<script lang="ts">
	import Mic from '@lucide/svelte/icons/mic';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Mic class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Mic>
