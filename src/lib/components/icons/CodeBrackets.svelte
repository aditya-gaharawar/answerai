<script lang="ts">
	import CodeXml from '@lucide/svelte/icons/code-xml';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<CodeXml class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"></CodeXml>
