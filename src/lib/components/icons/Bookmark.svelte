<script lang="ts">
	import Bookmark from '@lucide/svelte/icons/bookmark';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<Bookmark class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Bookmark>
