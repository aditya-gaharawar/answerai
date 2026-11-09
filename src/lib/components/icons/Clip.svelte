<script lang="ts">
	import Paperclip from '@lucide/svelte/icons/paperclip';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Paperclip class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Paperclip>
