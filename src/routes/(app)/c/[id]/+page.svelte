<script lang="ts">
	import { page } from '$lib/stores/page';

	import Chat from '$lib/components/chat/Chat.svelte';
</script>

<Chat chatIdProp={$page.params.id} />
