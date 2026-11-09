<script lang="ts">
	import EyeOff from '@lucide/svelte/icons/eye-off';
	export let className = 'w-4 h-4';
	export let strokeWidth = '1.5';
</script>

<EyeOff class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></EyeOff>
