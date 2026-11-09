<script lang="ts">
	import MessageCircle from '@lucide/svelte/icons/message-circle';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<MessageCircle class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></MessageCircle>
