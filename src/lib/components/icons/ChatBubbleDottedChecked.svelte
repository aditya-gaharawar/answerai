<script lang="ts">
	import MessageSquareDot from '@lucide/svelte/icons/message-square-dot';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<MessageSquareDot class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></MessageSquareDot>
