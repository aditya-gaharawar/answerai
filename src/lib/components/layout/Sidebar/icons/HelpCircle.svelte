<script lang="ts">
	import CircleQuestionMark from '@lucide/svelte/icons/circle-question-mark';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<CircleQuestionMark class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></CircleQuestionMark>
