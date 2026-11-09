<script lang="ts">
	import Combine from '@lucide/svelte/icons/combine';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Combine class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Combine>
