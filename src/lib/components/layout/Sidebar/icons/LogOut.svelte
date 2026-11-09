<script lang="ts">
	import LogOut from '@lucide/svelte/icons/log-out';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<LogOut class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></LogOut>
