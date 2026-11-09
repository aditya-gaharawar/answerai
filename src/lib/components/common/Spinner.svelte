<script lang="ts">
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	export let className: string = 'size-4';
</script>

<div class="flex justify-center text-center">
	<LoaderCircle class={`animate-spin ${className}`} strokeWidth={1.5} aria-hidden="true" />
</div>
