<script lang="ts">
	import Workflow from '@lucide/svelte/icons/workflow';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Workflow class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Workflow>
