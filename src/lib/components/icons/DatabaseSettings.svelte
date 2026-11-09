<script lang="ts">
	import DatabaseZap from '@lucide/svelte/icons/database-zap';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<DatabaseZap class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></DatabaseZap>
