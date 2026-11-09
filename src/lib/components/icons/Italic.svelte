<script lang="ts">
	import Italic from '@lucide/svelte/icons/italic';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Italic class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Italic>
