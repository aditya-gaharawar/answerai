<script lang="ts">
	import LayoutDashboard from '@lucide/svelte/icons/layout-dashboard';
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<LayoutDashboard class={className} strokeWidth={Number(strokeWidth)} aria-hidden="true"
></LayoutDashboard>
