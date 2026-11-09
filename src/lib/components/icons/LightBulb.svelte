<script lang="ts">
	import Lightbulb from '@lucide/svelte/icons/lightbulb';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Lightbulb class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Lightbulb>
