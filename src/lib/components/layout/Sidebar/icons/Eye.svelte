<script lang="ts">
	import Eye from '@lucide/svelte/icons/eye';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Eye class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Eye>
