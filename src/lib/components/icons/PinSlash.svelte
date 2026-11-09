<script lang="ts">
	import PinOff from '@lucide/svelte/icons/pin-off';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<PinOff class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></PinOff>
