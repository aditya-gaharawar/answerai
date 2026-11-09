<script lang="ts">
	import Clipboard from '@lucide/svelte/icons/clipboard';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Clipboard class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Clipboard>
