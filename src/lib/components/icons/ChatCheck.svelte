<script lang="ts">
	import MessageSquareCheck from '@lucide/svelte/icons/message-square-check';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<MessageSquareCheck class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></MessageSquareCheck>
