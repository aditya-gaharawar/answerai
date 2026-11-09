<script lang="ts">
	import MessageSquarePlus from '@lucide/svelte/icons/message-square-plus';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<MessageSquarePlus class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></MessageSquarePlus>
