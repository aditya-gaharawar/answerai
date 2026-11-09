<script lang="ts">
	import ListTodo from '@lucide/svelte/icons/list-todo';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<ListTodo class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></ListTodo>
