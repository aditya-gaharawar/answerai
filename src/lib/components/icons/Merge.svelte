<script lang="ts">
	import GitMerge from '@lucide/svelte/icons/git-merge';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<GitMerge class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></GitMerge>
