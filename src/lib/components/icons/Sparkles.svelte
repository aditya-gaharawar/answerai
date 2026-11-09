<script lang="ts">
	import Sparkles from '@lucide/svelte/icons/sparkles';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Sparkles class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Sparkles>
