<script lang="ts">
	import LogOut from '@lucide/svelte/icons/log-out';
	export let className = 'w-5 h-5';
	export let strokeWidth = '1.5';
</script>

<LogOut class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></LogOut>
