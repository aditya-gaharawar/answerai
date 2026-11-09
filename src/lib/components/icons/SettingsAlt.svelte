<script lang="ts">
	import Settings2 from '@lucide/svelte/icons/settings-2';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Settings2 class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Settings2>
