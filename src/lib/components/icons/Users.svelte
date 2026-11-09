<script lang="ts">
	import Users from '@lucide/svelte/icons/users';
	export let className = 'size-3';
	export let strokeWidth = '1.5';
</script>

<Users class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Users>
