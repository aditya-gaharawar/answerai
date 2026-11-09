<script lang="ts">
	import ListTodo from '@lucide/svelte/icons/list-todo';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<ListTodo class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></ListTodo>
