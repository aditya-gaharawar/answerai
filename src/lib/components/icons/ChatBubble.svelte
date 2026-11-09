<script lang="ts">
	import MessageSquare from '@lucide/svelte/icons/message-square';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<MessageSquare class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></MessageSquare>
