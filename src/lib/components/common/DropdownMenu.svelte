<script lang="ts">
	export let className = '';
	export let style = '';
</script>

<div
	class={`aai-menu aai-glass app-dropdown-menu z-50 ${className} [&>button]:flex [&>button]:w-full [&>button]:items-center [&>button]:gap-2 [&>button]:px-2 [&>a]:flex [&>a]:w-full [&>a]:items-center [&>a]:gap-2 [&>a]:px-2 [&>button_svg]:size-4 [&>a_svg]:size-4 [&>hr]:my-1 [&>hr]:mx-1`}
	{style}
>
	<slot />
</div>
