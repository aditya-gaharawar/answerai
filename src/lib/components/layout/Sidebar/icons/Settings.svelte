<script lang="ts">
	import Settings from '@lucide/svelte/icons/settings';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Settings class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Settings>
