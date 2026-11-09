<script lang="ts">
	import Tag from '@lucide/svelte/icons/tag';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Tag class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Tag>
