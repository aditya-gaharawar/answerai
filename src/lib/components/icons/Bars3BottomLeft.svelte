<script lang="ts">
	import TextAlignStart from '@lucide/svelte/icons/text-align-start';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<TextAlignStart class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></TextAlignStart>
