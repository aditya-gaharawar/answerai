<script lang="ts">
	import Plus from '@lucide/svelte/icons/plus';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Plus class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Plus>
