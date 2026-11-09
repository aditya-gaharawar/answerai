<script lang="ts">
	import MessagesSquare from '@lucide/svelte/icons/messages-square';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<MessagesSquare class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></MessagesSquare>
