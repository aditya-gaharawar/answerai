<script lang="ts">
	import BookmarkX from '@lucide/svelte/icons/bookmark-x';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<BookmarkX class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></BookmarkX>
