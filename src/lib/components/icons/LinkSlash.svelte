<script lang="ts">
	import Unlink from '@lucide/svelte/icons/unlink';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Unlink class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Unlink>
