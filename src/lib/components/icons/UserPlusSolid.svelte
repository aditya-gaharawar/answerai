<script lang="ts">
	import UserRoundPlus from '@lucide/svelte/icons/user-round-plus';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<UserRoundPlus class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></UserRoundPlus>
