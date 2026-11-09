<script lang="ts">
	import PanelLeft from '@lucide/svelte/icons/panel-left';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<PanelLeft class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></PanelLeft>
