<script lang="ts">
	import Zap from '@lucide/svelte/icons/zap';
	export let className = 'size-3';
	export let strokeWidth = '1.5';
</script>

<Zap class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Zap>
