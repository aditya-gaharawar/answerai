<script lang="ts">
	import MessageSquareText from '@lucide/svelte/icons/message-square-text';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<MessageSquareText class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></MessageSquareText>
