<script lang="ts">
	import AlignVerticalJustifyCenter from '@lucide/svelte/icons/align-vertical-justify-center';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<AlignVerticalJustifyCenter class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></AlignVerticalJustifyCenter>
