<script lang="ts">
	import Save from '@lucide/svelte/icons/save';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Save class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Save>
