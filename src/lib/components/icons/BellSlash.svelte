<script lang="ts">
	import BellOff from '@lucide/svelte/icons/bell-off';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<BellOff class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></BellOff>
