<script lang="ts">
	import Play from '@lucide/svelte/icons/play';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<Play class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Play>
