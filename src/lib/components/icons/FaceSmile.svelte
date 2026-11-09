<script lang="ts">
	import FaceSlightlySmiling from '@lucide/svelte/icons/face-slightly-smiling';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<FaceSlightlySmiling class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></FaceSlightlySmiling>
