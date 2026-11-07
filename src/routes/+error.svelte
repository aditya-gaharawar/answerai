<script>
	import { errorText } from '$lib/utils/errorText';

	import { page } from '$lib/stores/page';
</script>

<div class=" bg-white dark:bg-gray-800 min-h-screen">
	<div class=" flex h-full">
		<div class="m-auto my-10 dark:text-gray-300 text-3xl font-normal">
			{$page.status}: {errorText($page.error)}
		</div>
	</div>
</div>
