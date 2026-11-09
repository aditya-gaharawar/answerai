<script lang="ts">
	import Eye from '@lucide/svelte/icons/eye';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Eye class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Eye>
