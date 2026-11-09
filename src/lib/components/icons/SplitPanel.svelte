<script lang="ts">
	import PanelsTopLeft from '@lucide/svelte/icons/panels-top-left';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<PanelsTopLeft class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></PanelsTopLeft>
