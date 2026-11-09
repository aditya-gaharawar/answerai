<script lang="ts">
	import Underline from '@lucide/svelte/icons/underline';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Underline class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Underline>
