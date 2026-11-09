<script lang="ts">
	import { settings } from '$lib/stores';
	export let id: string | undefined = undefined;
</script>

<div
	{id}
	dir={$settings?.chatDirection === 'RTL'
		? 'rtl'
		: $settings?.chatDirection === 'LTR'
			? 'ltr'
			: 'auto'}
	class="aai-composer flex-1 flex flex-col relative w-full transition"
>
	<slot />
</div>
