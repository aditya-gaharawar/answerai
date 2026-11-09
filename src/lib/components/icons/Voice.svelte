<script lang="ts">
	import AudioLines from '@lucide/svelte/icons/audio-lines';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<AudioLines class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></AudioLines>
