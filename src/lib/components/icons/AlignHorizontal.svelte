<script lang="ts">
	import AlignHorizontalJustifyCenter from '@lucide/svelte/icons/align-horizontal-justify-center';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<AlignHorizontalJustifyCenter class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></AlignHorizontalJustifyCenter>
