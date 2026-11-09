<script lang="ts">
	import CircleUserRound from '@lucide/svelte/icons/circle-user-round';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<CircleUserRound class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></CircleUserRound>
