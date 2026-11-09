<script lang="ts">
	import MessageSquareDashed from '@lucide/svelte/icons/message-square-dashed';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<MessageSquareDashed class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></MessageSquareDashed>
