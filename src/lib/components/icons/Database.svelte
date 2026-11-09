<script lang="ts">
	import Database from '@lucide/svelte/icons/database';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Database class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Database>
