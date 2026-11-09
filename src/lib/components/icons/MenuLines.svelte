<script lang="ts">
	import Menu from '@lucide/svelte/icons/menu';
	export let className = 'size-5';
	export let strokeWidth = '1.5';
</script>

<Menu class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Menu>
