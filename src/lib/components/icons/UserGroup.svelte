<script lang="ts">
	import Users from '@lucide/svelte/icons/users';
	export let className = 'w-5 h-5';
	export let strokeWidth = '1.5';
</script>

<Users class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></Users>
