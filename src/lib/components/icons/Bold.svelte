<script lang="ts">
	import LetterB from '@lucide/svelte/icons/letter-b';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<LetterB class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></LetterB>
