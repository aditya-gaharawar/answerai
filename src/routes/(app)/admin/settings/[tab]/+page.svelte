<script>
	import { goto } from '$app/navigation';
	import { page } from '$lib/stores/page';
	import { onMount } from 'svelte';

	onMount(() => {
		const params = new URLSearchParams($page.url.searchParams.toString());
		params.set('settings', `admin:${$page.params.tab ?? 'general'}`);
		goto(`/?${params.toString()}`, { replaceState: true });
	});
</script>
