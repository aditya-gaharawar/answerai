<script lang="ts">
	import User from '@lucide/svelte/icons/user';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<User class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></User>
