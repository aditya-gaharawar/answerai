<script lang="ts">
	import BookOpen from '@lucide/svelte/icons/book-open';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<BookOpen class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></BookOpen>
